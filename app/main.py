from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel,EmailStr
from datetime import datetime
from typing import Optional
from geopy.geocoders import Nominatim
from app.core.security import get_password_hash, verify_password
from app.services.astronomy import CelestialEngine
from app.services.ai_engine import GeminiInterpreter
from app.api.endpoints import auth, profiles # Router'larımızı import ediyoruz
from app.db.database import engine, Base, get_db
from sqlalchemy.orm import Session
from app.models import models

# this line will create the tables in the database based on our SQLAlchemy models (User, Profile, Analysis)
models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="AstroLogic API")

app.include_router(auth.router)
app.include_router(profiles.router)

@app.get("/")
async def root():
    return {"message": "AstroLogic Modüler API is working!"}

@app.post("/chat")
async def chat_with_chart(profile_id: int, question: str):
    # This is where we will implement the "Ask about this chart" logic later
    return {"message": "Chat feature coming in the next sprint!"}