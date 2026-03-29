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
    if data.lat is None or data.lon is None:
        location = geolocator.geocode(data.city)
        if not location:
            raise HTTPException(status_code=400, detail="Invalid city name, unable to geocode.")
        lat, lon = location.latitude, location.longitude
    else:
        lat, lon = data.lat, data.lon

    try:
        utc_birth_dt, effective_offset = local_wall_time_to_utc_naive(
            data.year,
            data.month,
            data.day,
            data.hour,
            data.minute,
            lat,
            lon,
            data.utc_offset,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    new_profile = models.Profile(
        user_id=current_user.id,
        name=data.name,
        city=data.city,
        birth_date=utc_birth_dt,
        latitude=lat,
        longitude=lon,
        utc_offset_hours=effective_offset,
    )

    try:
        db.add(new_profile)
        db.flush()

        # Engine expects naive UTC + utc_offset=0 (offset already applied to wall time).
        engine = CelestialEngine(utc_birth_dt, lat, lon, utc_offset=0.0)
        chart_points = engine.get_full_chart()

        interpreter = GeminiInterpreter()
        report = interpreter.generate_standard_report(chart_points, data.name)
        summary = (report[:500] + "…") if len(report) > 500 else report

        new_analysis = models.Analysis(
            profile_id=new_profile.id,
            report_content=report,
            summary=summary,
            chart_data=chart_points,
        )
        db.add(new_analysis)
        db.commit()
        db.refresh(new_profile)
        db.refresh(new_analysis)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error while saving profile or analysis.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "profile created and analysis completed",
        "profile_id": new_profile.id,
        "analysis": report,
        "chart_data": chart_points,
    }


@router.post("/analyze")
async def analyze_birth_chart(
    data: BirthData,
    current_user: models.User = Depends(get_current_user),
):
    try:
        if data.lat is None or data.lon is None:
            location = geolocator.geocode(data.city)
            if not location:
                raise HTTPException(status_code=400, detail="Invalid city name, unable to geocode.")
            current_lat = location.latitude
            current_lon = location.longitude
        else:
            current_lat = data.lat
            current_lon = data.lon

        try:
            utc_birth_dt, _ = local_wall_time_to_utc_naive(
                data.year,
                data.month,
                data.day,
                data.hour,
                data.minute,
                current_lat,
                current_lon,
                data.utc_offset,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        astro_engine = CelestialEngine(utc_birth_dt, current_lat, current_lon, utc_offset=0.0)

        chart_points = astro_engine.get_full_chart()

        interpreter = GeminiInterpreter()
        report = interpreter.generate_standard_report(chart_points, data.name)

        return {
            "profile_name": data.name,
            "city": data.city,
            "latitude": current_lat,
            "longitude": current_lon,
            "analysis": report,
            "chart_data": chart_points,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
