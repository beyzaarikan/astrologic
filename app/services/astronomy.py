"""
Swiss Ephemeris wrapper. Julian day uses UT (UTC).

Callers should either:
- Pass a naive datetime that already represents the UTC instant and set utc_offset=0.0, or
- Pass naive local wall-clock components and set utc_offset to hours east of UTC (subtracts inside julday).

Do not mix both: applying utc_offset here after you already converted local→UTC double-applies the shift.
"""
import swisseph as swe
from datetime import datetime
import os

class CelestialEngine:
    ZODIAC_SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]

    def __init__(self, birth_date: datetime, lat: float, lon: float, utc_offset: float = 0.0):
        ephe_path = os.path.join(os.path.dirname(__file__), "ephe") 
        swe.set_ephe_path(ephe_path)
        
        self.birth_date = birth_date
        self.lat = lat
        self.lon = lon
        
        # Yerel saati UTC'ye çevirerek Julian Day hesapla
        # Örn: Saat 12:00, Offset +3 ise -> UTC Saat 09:00 olur.
        decimal_hour = birth_date.hour + birth_date.minute/60.0 - utc_offset
        self.julian_day = swe.julday(birth_date.year, birth_date.month, birth_date.day, decimal_hour)

    def get_planet_position(self, planet_id: int) -> dict:
        res = swe.calc_ut(self.julian_day, planet_id)
        longitude = res[0][0]
        
        return {
            "name": swe.get_planet_name(planet_id),
            "total_degree": longitude,
            "sign": self.ZODIAC_SIGNS[int(longitude / 30)],
            "degree_in_sign": round(longitude % 30, 2)
        }

    def calculate_aspects(self, planet_positions: list):
        """Gezegen listesini alır ve aralarındaki açıları döner."""
        aspects = []
        # Sadece ana gezegenleri ve Asc/MC'yi açılara dahil edelim (Ev sınırlarını hariç tutmak için)
        relevant_points = [p for p in planet_positions if "House" not in p["name"]]
        
        ASPECT_TYPES = [
            {"name": "Conjunction", "angle": 0, "orb": 8},
            {"name": "Opposition", "angle": 180, "orb": 8},
            {"name": "Trine", "angle": 120, "orb": 8},
            {"name": "Square", "angle": 90, "orb": 7},
            {"name": "Sextile", "angle": 60, "orb": 6},
        ]

        for i in range(len(relevant_points)):
            for j in range(i + 1, len(relevant_points)):
                p1 = relevant_points[i]
                p2 = relevant_points[j]
                
                diff = abs(p1["total_degree"] - p2["total_degree"])
                if diff > 180:
                    diff = 360 - diff

                for aspect in ASPECT_TYPES:
                    if abs(diff - aspect["angle"]) <= aspect["orb"]:
                        aspects.append({
                            "p1": p1["name"],
                            "p2": p2["name"],
                            "aspect": aspect["name"],
                            "orb": round(abs(diff - aspect["angle"]), 2)
                        })
        return aspects

    def get_full_chart(self):
        # 1. Gezegenleri hesapla
        planet_ids = [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS,
                      swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, 
                      swe.PLUTO, swe.CHIRON]
        
        chart_data = [self.get_planet_position(p) for p in planet_ids]
    
        # 2. Ascendant, MC ve Evleri hesapla
        houses, ascmc = swe.houses(self.julian_day, self.lat, self.lon, b'P')
        
        chart_data.append({"name": "Ascendant", "total_degree": ascmc[0],
                            "sign": self.ZODIAC_SIGNS[int(ascmc[0]/30)],
                            "degree_in_sign": round(ascmc[0] % 30, 2)})
        
        chart_data.append({"name": "MC", "total_degree": ascmc[1],
                            "sign": self.ZODIAC_SIGNS[int(ascmc[1]/30)],
                            "degree_in_sign": round(ascmc[1] % 30, 2)})

        # 3. Açıları hesapla (Evlerden önce hesaplıyoruz ki listeye evler karışmasın)
        aspects = self.calculate_aspects(chart_data)

        # 4. Ev sınırlarını ekle
        for i, cusp in enumerate(houses, 1):
            chart_data.append({"name": f"House {i} cusp", "total_degree": cusp,
                                "sign": self.ZODIAC_SIGNS[int(cusp/30)],
                                "degree_in_sign": round(cusp % 30, 2)})

        return {
            "points": chart_data,
            "aspects": aspects
        }