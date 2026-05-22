import time
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="zondata_scraper")

queries = [
    "Avenida Jose Ignacio de la Roza, San Juan, Argentina",
    "Ignacio de la Roza, San Juan, Argentina",
    "Güemes, San Juan, Argentina",
    "General Güemes, San Juan, Argentina",
]

for q in queries:
    try:
        loc = geolocator.geocode(q)
        if loc:
            print(f"[{q}] -> {loc.latitude}, {loc.longitude}")
        else:
            print(f"[{q}] -> No found")
        time.sleep(1.5)
    except Exception as e:
        print(f"[{q}] -> Error {e}")
