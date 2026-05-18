import os
import requests
import json
import time

# Helper para leer variables de entorno desde el archivo .env del proyecto
def get_env_variable(key, default=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = [
        os.path.join(base_dir, ".env"),
        ".env"
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith(key + "="):
                            val = line.split("=", 1)[1].strip()
                            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                                val = val[1:-1]
                            return val
            except Exception:
                pass
    return default

# URL dinámica desde el .env
APP_URL = get_env_variable("APP_URL", "http://zondata.test")
API_URL = f"{APP_URL.rstrip('/')}/api/incidents"

def send_incident(incident_data):
    try:
        response = requests.post(API_URL, json=incident_data, headers={'Accept': 'application/json'})
        if response.status_code == 201:
            print(f"Exito: {incident_data['titulo']}")
        else:
            print(f"Error {response.status_code}: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error de conexion: {e}")

if __name__ == "__main__":
    # Test data as requested by the user
    test_incident = {
        "etiqueta": "viento", 
        "titulo": "Caída de ramas en Plaza 25 de Mayo",
        "descripcion": "Ráfagas de 80km/h provocaron la caída de tres ramas grandes afectando la circulación peatonal.",
        "latitud": -31.5375,
        "longitud": -68.5364,
        "fuente_nombre": "Diario de Cuyo",
        "fuente_url": "https://www.diariodecuyo.com.ar/noticia...",
        "verificado": False
    }

    # Additional test data
    test_incident_2 = {
        "etiqueta": "corte", 
        "titulo": "Corte de energía en Rivadavia",
        "descripcion": "Transformador dañado por las ráfagas de viento zonda. Zonas aledañas sin servicio.",
        "latitud": -31.5200,
        "longitud": -68.5800,
        "fuente_nombre": "Energía San Juan",
        "fuente_url": "https://twitter.com/EnergiaSanJuan",
        "verificado": True
    }
    
    print("Iniciando motor de ingesta (Prueba Zonda)...")
    send_incident(test_incident)
    time.sleep(1)
    send_incident(test_incident_2)
    print("Ingesta finalizada.")
