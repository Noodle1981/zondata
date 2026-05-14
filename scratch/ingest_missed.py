import requests
import json

API_URL = "http://zondata.test/api/incidents"

incident = {
    "etiqueta": "choque",
    "titulo": "Caos vehicular en Ruta 20: una frenada provocó un choque múltiple frente al Aeropuerto",
    "descripcion": "Un fuerte siniestro vial se produjo en la mañana de este miércoles sobre la Ruta 20, a metros del Aeropuerto de San Juan. Hubo varios vehículos involucrados.",
    "latitud": -31.6573,
    "longitud": -68.2695893,
    "is_approximate": False,
    "fuente_nombre": "Tiempo de San Juan",
    "fuente_url": "https://www.tiempodesanjuan.com/policiales/caos-vehicular-ruta-20-una-frenada-provoco-un-choque-multiple-frente-al-aeropuerto-n430107",
    "verificado": False,
    "event_date": "2026-05-13 10:00:00"
}

try:
    res = requests.post(API_URL, json=incident, headers={'Accept': 'application/json'})
    if res.status_code in [200, 201]:
        print(f"Éxito: {res.status_code}")
    else:
        print(f"Error {res.status_code}: {res.text}")
except Exception as e:
    print(f"Falla: {e}")
