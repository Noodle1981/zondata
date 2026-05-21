import sys
import os
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="zondata_test")

queries = [
    "Ruta 40, San Juan, Argentina",
    "Ruta 40 y Calle 9, San Juan, Argentina",
    "Ruta 40 entre Calle 9 y 10, San Juan, Argentina",
    "Ruta 40 y Calle 9, Pocito, San Juan, Argentina",
    "Calle 9, Pocito, San Juan, Argentina",
    "Ruta Nacional 40 & Calle 9, Pocito, San Juan, Argentina"
]

for q in queries:
    try:
        loc = geolocator.geocode(q, timeout=10)
        if loc:
            print(f"QUERY: '{q}'")
            print(f"  Result: {loc.address}")
            print(f"  Coords: ({loc.latitude}, {loc.longitude})")
        else:
            print(f"QUERY: '{q}' -> NOT FOUND")
    except Exception as e:
        print(f"QUERY: '{q}' -> ERROR: {e}")
