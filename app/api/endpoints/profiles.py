from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from datetime import datetime
from geopy.geocoders import Nominatim

from app.db.database import get_db
from app.models import models
from app.schemas.profile import BirthData, ProfileCreate
from app.services.astronomy import CelestialEngine
from app.services.ai_engine import GeminiInterpreter
from app.api.dependencies import get_current_user 

geolocator = Nominatim(user_agent="astrologic_app")
router = APIRouter(prefix="/profiles", tags=["Profiles & Analysis"])

# db bağımlılığını Annotated ile tanımlayalım
db_dependency = Annotated[Session, Depends(get_db)]



@router.post("/create-and-analyze", status_code=status.HTTP_201_CREATED)
async def create_profile_and_run_analysis(data: ProfileCreate, db: db_dependency, current_user: Annotated[models.User, Depends(get_current_user)]):

    print(f"Sisteme giriş yapan kullanıcı: {current_user.email}")  # Debug için kullanıcı email'ini yazdırıyoruz
    # 1. Doğum tarihini oluştur
    birth_dt = datetime(data.year, data.month, data.day, data.hour, data.minute)
    
    # 2. Profili Veritabanına Kaydet
    new_profile = models.Profile(
        user_id=current_user.id,
        name=data.name,
        city=data.city,
        birth_date=birth_dt,
        latitude=data.lat,
        longitude=data.lon
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    # 3. Astronomi Hesaplamalarını Yap
    engine = CelestialEngine(birth_dt, data.lat, data.lon)
    chart_points = engine.get_full_chart()
    
    # 4. Gemini ile Analiz Et
    interpreter = GeminiInterpreter()
    report = interpreter.generate_standard_report(chart_points, data.name)
    
    # 5. Analizi Veritabanına Kaydet
    new_analysis = models.Analysis(
        profile_id=new_profile.id,
        report_content=report
    )
    db.add(new_analysis)
    db.commit()

    return {
        "message": "profile created and analysis completed",
        "profile_id": new_profile.id,
        "analysis": report
    }


@router.post("/analyze")
async def analyze_birth_chart(data: BirthData):
    try:
        # Eğer koordinatlar gelmemişse şehir isminden bul
        if data.lat is None or data.lon is None:
            location = geolocator.geocode(data.city)
            if not location:
                raise HTTPException(status_code=400, detail="Invalid city name, unable to geocode.")
            current_lat = location.latitude
            current_lon = location.longitude
        else:
            # Frontend'den hazır koordinat geldiyse onu kullan
            current_lat = data.lat
            current_lon = data.lon
        
        # send the birth data to the CelestialEngine to get the planetary positions
        birth_time = datetime(data.year, data.month, data.day, data.hour, data.minute)
        astro_engine = CelestialEngine(birth_time, current_lat, current_lon)
        
        chart_points = astro_engine.get_full_chart()
        
        interpreter = GeminiInterpreter()
        report = interpreter.generate_standard_report(chart_points, data.name)
        
        return {
            "profile_name": data.name,
            "city": data.city,
            "latitude": current_lat,
            "longitude": current_lon,
            "analysis": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

