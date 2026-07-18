import os
import sqlite3
import urllib.request
import re

# DB Path resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "database.sqlite")

SEASON_MAP = {
    "DJF": 1,
    "JFM": 2,
    "FMA": 3,
    "MAM": 4,
    "AMJ": 5,
    "MJJ": 6,
    "JJA": 7,
    "JAS": 8,
    "ASO": 9,
    "SON": 10,
    "OND": 11,
    "NDJ": 12
}

def init_enso_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enso_phases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            anomaly REAL NOT NULL,
            phase TEXT NOT NULL,
            UNIQUE(year, month)
        )
    """)
    conn.commit()
    conn.close()

def download_and_seed_enso():
    print("[ENSO] Inicializando base de datos...")
    init_enso_db()

    url = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
    print(f"[ENSO] Descargando datos ONI oficiales desde: {url}")
    
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8')
    except Exception as e:
        print(f"[ENSO][ERROR] No se pudo descargar desde NOAA ({e}). Se buscará un archivo local.")
        # Intentar leer desde cache local de step si existe, o usar fallback estático
        content = None

    if not content:
        # Fallback local o cache
        print("[ENSO] Intentando usar fallback estático...")
        # Generamos un pequeño dataset estático para los años recientes 2020-2026 para emergencias
        # pero trataremos de encontrar el archivo.
        return False

    # Procesar archivo ONI
    lines = content.split('\n')
    entries = []
    
    # Formato esperado:
    #  SEAS  YR   TOTAL   ANOM
    #   DJF 1950  24.72  -1.53
    for line in lines:
        line = line.strip()
        if not line or line.startswith("SEAS"):
            continue
        
        parts = re.split(r'\s+', line)
        if len(parts) >= 4:
            seas, yr_str, total_str, anom_str = parts[0], parts[1], parts[2], parts[3]
            try:
                year = int(yr_str)
                month = SEASON_MAP.get(seas)
                if not month:
                    continue
                anomaly = float(anom_str)
                
                # Clasificación oficial ENSO
                if anomaly >= 0.5:
                    phase = "niño"
                elif anomaly <= -0.5:
                    phase = "niña"
                else:
                    phase = "neutro"
                    
                entries.append((year, month, anomaly, phase))
            except ValueError:
                continue

    if not entries:
        print("[ENSO][WARNING] No se encontraron entradas válidas para importar.")
        return False

    print(f"[ENSO] Procesadas {len(entries)} entradas mensuales. Guardando en SQLite...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.executemany("""
        INSERT OR REPLACE INTO enso_phases (year, month, anomaly, phase)
        VALUES (?, ?, ?, ?)
    """, entries)
    
    conn.commit()
    
    # Verificar cantidad total
    cursor.execute("SELECT COUNT(*) FROM enso_phases")
    count = cursor.fetchone()[0]
    conn.close()
    
    print(f"[ENSO][OK] Sembrado completado. Total registros en enso_phases: {count}")
    return True

if __name__ == "__main__":
    download_and_seed_enso()
