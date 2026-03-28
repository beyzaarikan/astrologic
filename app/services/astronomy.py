import swisseph as swe
from datetime import datetime
import os

class PlanetPosition:
    """A simple Data Object for a Planet's state."""
    def __init__(self, name: str, degree: float, sign: str, house: int):
        self.name = name
        self.degree = degree
        self.sign = sign
        self.house = house

class CelestialEngine:
    """
    The main OOP Engine for astronomical calculations.
    This class is responsible for:
    - Converting birth data into Julian Day (using Swiss Ephemeris)
    - Calculating planetary positions (longitude, sign, degree in sign)   
    
    """
    
    ZODIAC_SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]

    def __init__(self, birth_date: datetime, lat: float, lon: float):
        ephe_path = os.path.join(os.path.dirname(__file__), "ephe") 
        swe.set_ephe_path(ephe_path) # Kütüphaneye yolu tanıt
        base_dir = os.path.dirname(__file__)
    
        self.birth_date = birth_date
        self.lat = lat
        self.lon = lon
        # Convert birth_date to Julian Day (required by Swiss Ephemeris)
        self.julian_day = swe.julday(
            birth_date.year, birth_date.month, birth_date.day, 
            birth_date.hour + birth_date.minute/60.0
        )

    def get_planet_position(self, planet_id: int) -> dict:
        """Calculates position for a specific planet (e.g., swe.SUN)."""
        res = swe.calc_ut(self.julian_day, planet_id)
        longitude = res[0][0]
        
        sign_index = int(longitude / 30)
        degree_in_sign = longitude % 30
        
        return {
            "name": swe.get_planet_name(planet_id),
            "total_degree": longitude,
            "sign": self.ZODIAC_SIGNS[sign_index],
            "degree_in_sign": round(degree_in_sign, 2)
        }

    def get_full_chart(self):
        """Returns a complete technical summary of the chart."""
        planets_to_calculate = [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS,swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO , swe.ASC, swe.MC, swe.CHIRON,swe.VERTEX]
        chart_data = []
        
        for p_id in planets_to_calculate:
            chart_data.append(self.get_planet_position(p_id))
            
        return chart_data