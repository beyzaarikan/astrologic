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
    lat: Optional[float] = None
    lon: Optional[float] = None
    # Hours east of UTC (e.g. +3.0 Istanbul, -5.0 New York). Applied to wall-clock birth time.
    utc_offset: float = 0.0


class BirthData(BaseModel):
    name: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    city: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    utc_offset: float = 0.0
