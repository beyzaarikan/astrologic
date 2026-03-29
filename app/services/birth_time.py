"""Convert local birth wall time to naive UTC for Swiss Ephemeris.

If ``utc_offset_hours`` is provided, a fixed offset is used (no DST).
If omitted, the IANA timezone at (lat, lon) is used so users only need date, time, and place.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo

_tf = TimezoneFinder()


def local_wall_time_to_utc_naive(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lon: float,
    utc_offset_hours: Optional[float],
) -> Tuple[datetime, float]:
    """
    Returns (utc_naive_instant, effective_offset_hours_at_birth).

    ``effective_offset_hours_at_birth`` is stored on Profile for display/debug;
    for fixed-offset mode it equals the user-supplied value.
    """
    local_naive = datetime(year, month, day, hour, minute)

    if utc_offset_hours is not None:
        utc_naive = local_naive - timedelta(hours=utc_offset_hours)
        return utc_naive, utc_offset_hours

    tz_name = _tf.timezone_at(lng=lon, lat=lat)
    if not tz_name:
        raise ValueError(
            "Could not determine timezone from coordinates. "
            "Try a clearer city name, add latitude/longitude, or pass utc_offset explicitly."
        )

    zi = ZoneInfo(tz_name)
    local_aware = local_naive.replace(tzinfo=zi)
    utc_aware = local_aware.astimezone(timezone.utc)
    utc_naive = utc_aware.replace(tzinfo=None)

    off = local_aware.utcoffset()
    effective = off.total_seconds() / 3600.0 if off is not None else 0.0
    return utc_naive, effective
