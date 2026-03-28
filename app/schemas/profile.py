from pydantic import BaseModel
from typing import Optional

class ProfileCreate(BaseModel):
    name: str
    city: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    lat: float
    lon: float

class BirthData(BaseModel):
    name: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    city: str
    lat: Optional[float] = None  # Eğer varsa kullanırız
    lon: Optional[float] = None
