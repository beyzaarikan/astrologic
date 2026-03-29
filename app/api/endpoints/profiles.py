from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Annotated
from datetime import datetime
from geopy.geocoders import Nominatim

from app.db.database import get_db
from app.models import models
from app.schemas.profile import BirthData, ProfileCreate
from app.services.astronomy import CelestialEngine
from app.services.ai_engine import GeminiInterpreter
from app.services.birth_time import local_wall_time_to_utc_naive
from app.api.dependencies import get_current_user

geolocator = Nominatim(user_agent="astrologic_app")
router = APIRouter(prefix="/profiles", tags=["Profiles & Analysis"])

db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/get-user-profiles", status_code=status.HTTP_200_OK)
async def get_user_profiles(
    db: db_dependency,
    current_user: models.User = Depends(get_current_user),
):
    profiles = db.query(models.Profile).filter(models.Profile.user_id == current_user.id).all()

    if not profiles:
        return {"message": "could not find any profiles for this user.", "profiles": []}

    return {
        "user": current_user.email,
        "profiles": profiles,
    }


@router.get("/get-profile-detail/{profile_id}", status_code=status.HTTP_200_OK)
async def get_profile_detail(
    profile_id: int,
    db: db_dependency,
    current_user: models.User = Depends(get_current_user),
):
    profile = db.query(models.Profile).filter(
        models.Profile.id == profile_id,
        models.Profile.user_id == current_user.id,
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="could not find the profile.")

    analyses = (
        db.query(models.Analysis)
        .filter(models.Analysis.profile_id == profile.id)
        .order_by(models.Analysis.id.desc())
        .all()
    )

    return {
        "profile": profile,
        "analyses": analyses,
    }


@router.post("/create-and-analyze", status_code=status.HTTP_201_CREATED)
async def create_profile_and_run_analysis(
    data: ProfileCreate,
    db: db_dependency,
    current_user: models.User = Depends(get_current_user),
):
    # 1. Geocoding ve Zaman Dönüşümü (Mevcut kodun aynı)
    if data.lat is None or data.lon is None:
        location = geolocator.geocode(data.city)
        if not location:
            raise HTTPException(status_code=400, detail="Invalid city name.")
        lat, lon = location.latitude, location.longitude
    else:
        lat, lon = data.lat, data.lon

    try:
        utc_birth_dt, effective_offset = local_wall_time_to_utc_naive(
            data.year, data.month, data.day, data.hour, data.minute, lat, lon, data.utc_offset
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. CACHE KONTROLÜ (Geliştirilmiş)
    # Aynı isim ve doğum tarihine sahip mevcut bir analiz var mı?
    existing_data = db.query(models.Analysis).join(models.Profile).filter(
        models.Profile.user_id == current_user.id,
        models.Profile.name == data.name,
        models.Profile.birth_date == utc_birth_dt
    ).first()

    if existing_data:
        return {
            "message": "Analysis retrieved from cache",
            "profile_id": existing_data.profile_id,
            "analysis": existing_data.report_content,
            "chart_data": existing_data.chart_data # Frontend hata almasın diye ekledik
        }

    # 3. YENİ ANALİZ SÜRECİ
    try:
        # Önce profili oluştur
        new_profile = models.Profile(
            user_id=current_user.id,
            name=data.name,
            city=data.city,
            birth_date=utc_birth_dt,
            latitude=lat,
            longitude=lon,
            utc_offset_hours=effective_offset,
        )
        db.add(new_profile)
        db.flush() 

        # Gemini ve Hesaplama
        engine = CelestialEngine(utc_birth_dt, lat, lon, utc_offset=0.0)
        chart_points = engine.get_full_chart()

        interpreter = GeminiInterpreter()
        report = interpreter.generate_standard_report(chart_points, data.name)
        
        # Analizi kaydet
        new_analysis = models.Analysis(
            profile_id=new_profile.id,
            report_content=report,
            summary=report[:500] if len(report) > 500 else report,
            chart_data=chart_points,
        )
        db.add(new_analysis)
        db.commit()
        
        return {
            "message": "profile created and analysis completed",
            "profile_id": new_profile.id,
            "analysis": report,
            "chart_data": chart_points,
        }

    except Exception as e:
        db.rollback()
        # Eğer hata Gemini'den geliyorsa (429 gibi), kullanıcıya bunu bildir
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            raise HTTPException(status_code=429, detail="The stars are busy right now (API Limit). Please try again in a minute.")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")