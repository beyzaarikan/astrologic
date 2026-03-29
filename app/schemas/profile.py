from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class ProfileCreate(BaseModel):
    """Birth data for a new chart. Send as JSON (Content-Type: application/json)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Jane Doe",
                    "city": "Istanbul",
                    "year": 1990,
                    "month": 5,
                    "day": 15,
                    "hour": 14,
                    "minute": 30,
                }
            ]
        }
    )

    name: str
    city: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    lat: Optional[float] = Field(default=None, description="Optional; omit to geocode from city")
    lon: Optional[float] = Field(default=None, description="Optional; omit to geocode from city")
    utc_offset: Optional[float] = Field(
        default=None,
        description=(
            "Optional hours east of UTC for fixed offset (no DST). "
            "Omit this field to auto-detect timezone from latitude/longitude (recommended)."
        ),
    )


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
    utc_offset: Optional[float] = Field(
        default=None,
        description="Optional; omit to infer timezone from coordinates.",
    )
