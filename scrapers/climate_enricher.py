import os
import sqlite3
import json
import urllib.request
import urllib.parse
from datetime import datetime

# DB Path resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "database.sqlite")

def get_enso_phase_from_db(year, month):
    """Consulta la fase ENSO desde la tabla local enso_phases"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT phase FROM enso_phases WHERE year = ? AND month = ?", 
            (year, month)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
    except Exception as e:
        print(f"[CLIMATE][ENSO-DB][ERROR] No se pudo leer ENSO de la DB ({e})")
    return "neutro"

def fetch_open_meteo_data(lat, lon, date_str):
    """
    Consulta Open-Meteo para obtener datos climáticos históricos.
    Intenta primero con el Archive API. Si falla (por ser fecha muy reciente),
    intenta con el Forecast API como fallback.
    """
    # Intentar parsear fecha para asegurar formato YYYY-MM-DD
    try:
        dt = datetime.strptime(date_str.split(" ")[0], "%Y-%m-%d")
        date_formatted = dt.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"[CLIMATE][ERROR] Fecha inválida '{date_str}': {e}")
        return None

    # URLs
    archive_url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={date_formatted}&end_date={date_formatted}&hourly=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_direction_10m&wind_speed_unit=kmh&timezone=America/Argentina/San_Juan"
    forecast_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&start_date={date_formatted}&end_date={date_formatted}&hourly=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_direction_10m&wind_speed_unit=kmh&timezone=America/Argentina/San_Juan"

    for url, api_name in [(archive_url, "Archive"), (forecast_url, "Forecast")]:
        try:
            print(f"[CLIMATE] Consultando Open-Meteo ({api_name}) para lat={lat}, lon={lon}, fecha={date_formatted}")
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                
            if "hourly" in res_data and res_data["hourly"].get("temperature_2m"):
                return res_data["hourly"]
        except Exception as e:
            print(f"[CLIMATE][WARNING] Falló consulta a Open-Meteo {api_name} API ({e})")
            continue

    return None

def enrich_incident_data(lat, lon, event_date_str):
    """
    Retorna un diccionario con datos de enriquecimiento climático para lat, lon y fecha dada.
    """
    # Valor por defecto
    result = {
        "temp_c": None,
        "humidity_pct": None,
        "wind_speed_kmh": None,
        "wind_direction_deg": None,
        "precipitation_mm": None,
        "uv_index": None,
        "weather_code": None,
        "enso_phase": "neutro"
    }

    try:
        dt = datetime.strptime(event_date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            dt = datetime.strptime(event_date_str.split(" ")[0], "%Y-%m-%d")
        except ValueError:
            print(f"[CLIMATE][ERROR] No se pudo parsear event_date_str '{event_date_str}'")
            return result

    # 1. Obtener fase ENSO
    result["enso_phase"] = get_enso_phase_from_db(dt.year, dt.month)

    # 2. Obtener datos de Open-Meteo
    hourly = fetch_open_meteo_data(lat, lon, event_date_str)
    if not hourly:
        print("[CLIMATE][WARNING] No se obtuvieron datos horarios de Open-Meteo.")
        return result

    # Analizar datos horarios.
    # Encontramos la hora con la máxima velocidad de viento para caracterizar el pico del evento
    wind_speeds = hourly.get("wind_speed_10m", [])
    if not wind_speeds:
        return result

    # Encontrar el índice de la velocidad de viento máxima
    max_wind_idx = 0
    max_wind = -1.0
    for idx, w in enumerate(wind_speeds):
        if w is not None and w > max_wind:
            max_wind = w
            max_wind_idx = idx

    # Extraer variables correspondientes a esa hora pico de viento
    try:
        result["wind_speed_kmh"] = float(wind_speeds[max_wind_idx])
        
        directions = hourly.get("wind_direction_10m", [])
        if directions and max_wind_idx < len(directions) and directions[max_wind_idx] is not None:
            result["wind_direction_deg"] = int(directions[max_wind_idx])

        temps = hourly.get("temperature_2m", [])
        if temps and max_wind_idx < len(temps) and temps[max_wind_idx] is not None:
            result["temp_c"] = float(temps[max_wind_idx])

        humidities = hourly.get("relative_humidity_2m", [])
        if humidities and max_wind_idx < len(humidities) and humidities[max_wind_idx] is not None:
            result["humidity_pct"] = float(humidities[max_wind_idx])

        codes = hourly.get("weather_code", [])
        if codes and max_wind_idx < len(codes) and codes[max_wind_idx] is not None:
            result["weather_code"] = str(codes[max_wind_idx])

        # Precipitación es la suma diaria acumulada
        precipitations = hourly.get("precipitation", [])
        valid_precip = [p for p in precipitations if p is not None]
        if valid_precip:
            result["precipitation_mm"] = float(sum(valid_precip))
            
    except Exception as e:
        print(f"[CLIMATE][ERROR] Excepción procesando métricas climáticas horarias ({e})")

    return result

def enrich_incident_in_db(incident_id):
    """Enriquece un incidente específico directamente en la BD SQLite"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT latitude, longitude, event_date FROM incidents WHERE id = ?", 
            (incident_id,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            print(f"[CLIMATE][ERROR] No se encontró el incidente {incident_id}")
            return False

        lat, lon, event_date_str = row
        conn.close()

        print(f"[CLIMATE] Iniciando enriquecimiento para incidente {incident_id} (Fecha: {event_date_str})")
        climate_data = enrich_incident_data(lat, lon, event_date_str)

        # Guardar en base de datos
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE incidents
            SET temp_c = ?,
                humidity_pct = ?,
                wind_speed_kmh = ?,
                wind_direction_deg = ?,
                precipitation_mm = ?,
                enso_phase = ?,
                weather_code = ?,
                climate_enriched = 1
            WHERE id = ?
        """, (
            climate_data["temp_c"],
            climate_data["humidity_pct"],
            climate_data["wind_speed_kmh"],
            climate_data["wind_direction_deg"],
            climate_data["precipitation_mm"],
            climate_data["enso_phase"],
            climate_data["weather_code"],
            incident_id
        ))
        conn.commit()
        conn.close()
        print(f"[CLIMATE][OK] Incidente {incident_id} enriquecido exitosamente: {climate_data}")
        return True
    except Exception as e:
        print(f"[CLIMATE][ERROR] No se pudo enriquecer el incidente {incident_id} en la DB ({e})")
        return False
