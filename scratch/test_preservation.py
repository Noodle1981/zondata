from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="zondata_test_preservation")

queries = [
    "calle Varas, Pampa del Chañar, Jáchal, San Juan, Argentina",
    "calle Varas, Pampa del Chañar, Jachal, San Juan, Argentina",
    "Varas, Pampa del Chañar, Jachal, San Juan, Argentina",
    "Pampa del Chañar, Jachal, San Juan, Argentina",
    "Jachal, San Juan, Argentina"
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
