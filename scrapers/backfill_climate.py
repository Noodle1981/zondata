"""
scrapers/backfill_climate.py
=============================
Backfill de datos climáticos para incidentes históricos sin enriquecer.

Recorre todos los incidentes con `climate_enriched = false` que tengan
fecha y coordenadas válidas, y consulta Open-Meteo Historical API para
obtener retroactivamente las variables meteorológicas del día del evento.

Características:
  - Reanudable: guarda progreso en backfill_progress.json
  - Respeta rate limit: 1 llamada/segundo (límite seguro de Open-Meteo)
  - No toca incidentes sin event_date o sin lat/lon del departamento
  - Log detallado en consola y en backfill_climate.log

Uso:
    python scrapers/backfill_climate.py
    python scrapers/backfill_climate.py --dry-run      (muestra cuántos hay, sin enriquecer)
    python scrapers/backfill_climate.py --limit 50     (enriquece solo los primeros 50)

Límites de Open-Meteo:
    - 10.000 llamadas/día en el plan gratuito
    - Sin API key requerida
    - Datos históricos disponibles desde 1940
"""

import sqlite3
import requests
import json
import os
import argparse
import time
import logging
from datetime import datetime

# ─── Configuración ─────────────────────────────────────────────────────────────

DB_PATH           = os.path.join(os.path.dirname(__file__), '..', 'database', 'database.sqlite')
PROGRESS_FILE     = os.path.join(os.path.dirname(__file__), 'backfill_progress.json')
LOG_FILE          = os.path.join(os.path.dirname(__file__), 'backfill_climate.log')
RATE_LIMIT_SLEEP  = 1.1   # segundos entre llamadas (seguro para Open-Meteo)
OPEN_METEO_URL    = "https://archive-api.open-meteo.com/v1/archive"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
    ]
)
log = logging.getLogger(__name__)

# ─── Coordenadas de respaldo por departamento (San Juan) ────────────────────────
# Se usan cuando el incidente no tiene lat/lon específico

DEPT_COORDS = {
    'Capital':       (-31.5375, -68.5364),
    'Chimbas':       (-31.4760, -68.5300),
    'Rawson':        (-31.5540, -68.4990),
    'Rivadavia':     (-31.5310, -68.5840),
    'Santa Lucía':   (-31.5180, -68.4850),
    'Pocito':        (-31.6580, -68.5290),
    'Sarmiento':     (-31.5870, -68.0500),
    'Albardón':      (-31.4210, -68.5590),
    'Angaco':        (-31.3830, -68.3720),
    'Caucete':       (-31.6620, -68.2820),
    'San Martín':    (-31.4310, -68.1880),
    '9 de Julio':    (-31.5250, -67.7680),
    '25 de Mayo':    (-31.5270, -67.6550),
    'Ullum':         (-31.4730, -68.7490),
    'Zonda':         (-31.5820, -68.7570),
    'Jáchal':        (-30.2340, -68.7460),
    'Iglesia':       (-30.4010, -69.2220),
    'Calingasta':    (-31.3360, -69.4190),
    'Valle Fértil':  (-30.6480, -67.4750),
    # Fallback general San Juan Capital
    'default':       (-31.5375, -68.5364),
}

# ─── Helpers ────────────────────────────────────────────────────────────────────

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'processed_ids': [], 'failed_ids': [], 'started_at': None, 'last_run': None}

def save_progress(progress):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def resolve_coords(incident, conn):
    """Obtiene coordenadas del incidente: primero usa las del registro, luego las del departamento."""
    # Si el incidente tiene coordenadas propias (se guardaron via geocoding)
    if incident['latitude'] and incident['longitude']:
        return float(incident['latitude']), float(incident['longitude'])

    # Usa las coordenadas del departamento como fallback
    if incident['department_id']:
        cur = conn.cursor()
        cur.execute("SELECT name FROM departments WHERE id = ?", (incident['department_id'],))
        dept = cur.fetchone()
        if dept and dept['name'] in DEPT_COORDS:
            return DEPT_COORDS[dept['name']]

    return DEPT_COORDS['default']

def resolve_enso_phase(event_date, conn):
    """Consulta la tabla local enso_phases para la fase ENSO de la fecha dada."""
    try:
        date = datetime.strptime(event_date[:10], '%Y-%m-%d')
        year, month = date.year, date.month
        cur = conn.cursor()
        cur.execute(
            "SELECT phase FROM enso_phases WHERE year = ? AND month = ?",
            (year, month)
        )
        row = cur.fetchone()
        if row:
            return row['phase']
    except Exception:
        pass
    return None

def fetch_open_meteo(lat, lon, date_str):
    """Llama a Open-Meteo Archive API y retorna datos climáticos del día."""
    params = {
        'latitude':      lat,
        'longitude':     lon,
        'start_date':    date_str,
        'end_date':      date_str,
        'hourly':        'temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,precipitation,weather_code',
        'timezone':      'America/Argentina/San_Juan',
        'wind_speed_unit': 'kmh',
    }
    try:
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        hourly = data.get('hourly', {})

        wind_speeds   = hourly.get('wind_speed_10m', [])
        wind_dirs     = hourly.get('wind_direction_10m', [])
        temps         = hourly.get('temperature_2m', [])
        humidities    = hourly.get('relative_humidity_2m', [])
        precipitations = hourly.get('precipitation', [])
        wcodes        = hourly.get('weather_code', [])

        if not wind_speeds:
            return None

        # Hora pico de viento
        peak_hour = max(range(len(wind_speeds)), key=lambda i: wind_speeds[i] or 0)

        return {
            'temp_c':           temps[peak_hour]          if peak_hour < len(temps)          else None,
            'humidity_pct':     humidities[peak_hour]     if peak_hour < len(humidities)     else None,
            'wind_speed_kmh':   wind_speeds[peak_hour]    if peak_hour < len(wind_speeds)    else None,
            'wind_direction_deg': wind_dirs[peak_hour]    if peak_hour < len(wind_dirs)      else None,
            'precipitation_mm': sum(p for p in precipitations if p),
            'weather_code':     str(int(wcodes[peak_hour])) if peak_hour < len(wcodes) and wcodes[peak_hour] is not None else None,
        }
    except Exception as e:
        log.warning(f"  [Open-Meteo] Error: {e}")
        return None

def enrich_incident(incident, climate_data, enso_phase, conn):
    """Actualiza el incidente en la BD con los datos climáticos."""
    cur = conn.cursor()
    cur.execute('''
        UPDATE incidents SET
            temp_c = ?,
            humidity_pct = ?,
            wind_speed_kmh = ?,
            wind_direction_deg = ?,
            precipitation_mm = ?,
            weather_code = ?,
            enso_phase = ?,
            climate_enriched = 1
        WHERE id = ?
    ''', (
        climate_data.get('temp_c'),
        climate_data.get('humidity_pct'),
        climate_data.get('wind_speed_kmh'),
        climate_data.get('wind_direction_deg'),
        climate_data.get('precipitation_mm'),
        climate_data.get('weather_code'),
        enso_phase,
        incident['id'],
    ))
    conn.commit()

# ─── Main ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Backfill de datos climáticos para incidentes históricos.')
    parser.add_argument('--dry-run', action='store_true', help='Solo muestra cuántos incidentes se procesarían.')
    parser.add_argument('--limit', type=int, default=0, help='Limitar a N incidentes (0 = sin límite).')
    parser.add_argument('--reset', action='store_true', help='Reinicia el archivo de progreso desde cero.')
    args = parser.parse_args()

    conn = get_conn()
    progress = load_progress()

    if args.reset:
        progress = {'processed_ids': [], 'failed_ids': [], 'started_at': None, 'last_run': None}
        save_progress(progress)
        log.info("🔄 Progreso reiniciado.")

    already_done = set(progress.get('processed_ids', []))
    failed_ids   = set(progress.get('failed_ids', []))

    # Obtener incidentes pendientes
    cur = conn.cursor()
    cur.execute('''
        SELECT i.id, i.title, i.event_date, i.latitude, i.longitude, i.department_id
        FROM incidents i
        WHERE i.climate_enriched = 0
          AND i.event_date IS NOT NULL
        ORDER BY i.event_date ASC
    ''')
    pending = [r for r in cur.fetchall() if r['id'] not in already_done]

    log.info("=" * 60)
    log.info("  ZonData — Backfill de Enriquecimiento Climático")
    log.info("=" * 60)
    log.info(f"  Incidentes pendientes de enriquecer: {len(pending)}")
    log.info(f"  Ya procesados en runs anteriores:    {len(already_done)}")
    log.info(f"  Fallidos en runs anteriores:         {len(failed_ids)}")

    if args.dry_run:
        log.info("\n  [DRY RUN] No se realizará ningún cambio.")
        if pending:
            log.info(f"\n  Primeros 10 pendientes:")
            for i in pending[:10]:
                log.info(f"    [ID {i['id']}] {i['event_date'][:10]} — {(i['title'] or '')[:60]}")
        conn.close()
        return

    if not pending:
        log.info("\n✅ Todos los incidentes ya están enriquecidos. No hay nada que hacer.")
        conn.close()
        return

    to_process = pending[:args.limit] if args.limit > 0 else pending
    log.info(f"\n  Procesando: {len(to_process)} incidentes...\n")

    if not progress.get('started_at'):
        progress['started_at'] = datetime.now().isoformat()

    success_count = 0
    fail_count    = 0

    for idx, incident in enumerate(to_process, 1):
        inc_id     = incident['id']
        date_str   = incident['event_date'][:10]
        title_short = (incident['title'] or 'sin título')[:55]

        log.info(f"[{idx}/{len(to_process)}] ID={inc_id} | {date_str} | {title_short}")

        try:
            lat, lon = resolve_coords(incident, conn)
            enso_phase = resolve_enso_phase(date_str, conn)

            climate_data = fetch_open_meteo(lat, lon, date_str)

            if climate_data:
                enrich_incident(incident, climate_data, enso_phase, conn)
                progress['processed_ids'].append(inc_id)
                success_count += 1
                log.info(f"  ✅ Enriquecido | Viento: {climate_data['wind_speed_kmh']} km/h | Temp: {climate_data['temp_c']}°C | ENSO: {enso_phase}")
            else:
                progress['failed_ids'].append(inc_id)
                fail_count += 1
                log.warning(f"  ⚠️  Sin datos de Open-Meteo para {date_str}")

        except Exception as e:
            progress['failed_ids'].append(inc_id)
            fail_count += 1
            log.error(f"  ❌ Error procesando ID={inc_id}: {e}")

        progress['last_run'] = datetime.now().isoformat()
        save_progress(progress)

        # Rate limit: respetar 1 llamada/segundo
        time.sleep(RATE_LIMIT_SLEEP)

    log.info("\n" + "=" * 60)
    log.info(f"  BACKFILL COMPLETADO")
    log.info(f"  Exitosos: {success_count} | Fallidos: {fail_count}")
    log.info(f"  Progreso guardado en: {PROGRESS_FILE}")
    log.info("=" * 60)

    conn.close()

if __name__ == '__main__':
    main()
