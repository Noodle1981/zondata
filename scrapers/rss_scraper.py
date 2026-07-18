import os
import hashlib
import requests
import xml.etree.ElementTree as ET
import time
import sqlite3
import re
import json
import unicodedata
from datetime import datetime
import html
from geopy.exc import GeocoderTimedOut  # Kept for potential future use

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GeminiTransientError(Exception):
    """Excepción lanzada cuando Gemini falla por problemas temporales de red, timeout o rate limit."""
    pass

def normalize_text(text):
    """Quita tildes/diacínticos para comparaciones robustas (e.g. 'arbol' == 'árbol')"""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

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

# Configuración Global - Usamos un User-Agent de navegador estándar para evitar bloqueos 403 (e.g. de Diario Huarpe)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Connection': 'keep-alive'
}

def get_headers(url):
    """
    Retorna los encabezados HTTP óptimos para cada medio.
    - Algunos medios (e.g. Diario Huarpe) bloquean peticiones que simulan ser Googlebot (403).
    - Otros medios (e.g. Diario Móvil debido a Cloudflare) bloquean agentes comunes de navegador sin entorno JS/TLS completo, pero permiten Googlebot por SEO.
    """
    if "diariomovil.info" in url:
        return {
            'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9',
            'Connection': 'keep-alive'
        }
    return HEADERS

API_URL = get_env_variable("APP_URL", "http://127.0.0.1:8000") + "/api/incidents"

# Contadores globales de llamadas a APIs en la ejecución actual para límites de seguridad
gemini_calls_in_run = 0
google_maps_calls_in_run = 0

from load_rules import load_rules, get_source_rule
RULES = load_rules()
# ─── Palabras de pre-filtro de TÍTULO ───────────────────────────────────────
# Estas listas son el PRIMER filtro: si el título no contiene ninguna de estas
# palabras, el artículo se descarta sin hacer deep fetch ni geocoding.
# Deben ser ESPECÍFICAS al hecho (no genéricas como "tránsito" o "vial").

# Viento / Zonda: palabras que indican daño concreto por viento y otros eventos climáticos
CONTEXT_WIND = [
    # Fenómenos
    "zonda", "viento zonda", "viento sur", "llegó el frío", "frente frío", "ráfagas", "vientos fuertes",
    "tormenta de viento", "temporal de viento", "temporal", "temporales",
    # Daños concretos (también aplica sin contexto de viento explícito)
    "voló el techo", "volaron techos", "voló un techo", "techo volado",
    "árbol caído", "arboles caidos", "árboles caídos", "árbol cayó",
    "cables caídos", "cables cortados", "sin luz por viento",
    "voladura de techo", "voladuras de techo",
    # Tormentas
    "tormenta", "tormenta eléctrica", "granizo", "granizos", "granizó", "lluvia", "lluvias", "lluvia torrencial", "lluvias fuertes",
    # Inundaciones
    "inundación", "inundó", "anegado", "anegamiento",
    # Crecientes
    "creciente", "crecidas", "crecida", "desbordó", "desborde del río", "quebrada crecida",
    # Derrumbes
    "derrumbe", "derrumbes", "desprendimiento", "alud", "piedras en la ruta", "caída de rocas",
    "corte de ruta", "ruta cortada por piedras", "ruta cortada por agua",
    # Nevada / Helada
    "nieve", "nevada", "nevadas", "nevó", "helada", "escarcha",
    # Fuego climático
    "incendio", "incendios", "incendio forestal", "hectáreas quemadas", "incendio de pastizales",
    # Calor extremo / Sequía
    "ola de calor", "sequía"
]

# Accidentes de tránsito: palabras que indican el hecho vial específico
CONTEXT_ACCIDENT = [
    # El siniestro en sí
    "accidente", "siniestro vial", "choque", "colisión", "colision",
    "vuelco", "volcó", "volco",
    "atropelló", "atropello", "atropellaron",
    "embistió", "embistio",
    "arrolló", "arrollo",
    "despistó", "despisto",
    "impactó", "impacto vial",
    "chocó", "choco", "chocar", "chocaron",
    # Víctimas en contexto vial
    "falleció en accidente", "murió en accidente", "víctima fatal en",
    "murió el motociclista", "falleció el motociclista",
    "murió el ciclista", "falleció el ciclista",
    "murió el conductor", "falleció el conductor",
    "murió el peatón", "falleció el peatón",
    "perdió la vida en",
    # Vehículos en contexto de siniestro
    "motociclista herido", "motociclista muerto", "motociclista fallecido",
    "ciclista herido", "ciclista muerto",
    "peatón herido", "peatón fallecido",
]

# Incendios: palabras que indican fuego real (no metafórico ni de armas)
CONTEXT_FIRE = [
    # El hecho en sí
    "incendio", "incendió", "incendio de", "se incendió", "incendian",
    "llamas", "en llamas",
    "ardió", "ardio", "arde",
    "quemó", "quemo", "quemaron",
    "siniestro ígneo", "siniestro igneo",
    "incineró", "incinero",
    # Daños concretos por fuego
    "casa quemada", "vivienda quemada", "vivienda incendiada",
    "auto incendiado", "vehículo incendiado", "camioneta incendiada",
    "pastizal en llamas", "pastizales en llamas", "campo en llamas",
    "quemados", "incinerados",
    # Intervención de bomberos en escena (no capacitaciones)
    "bomberos combaten", "bomberos controlaron", "bomberos sofocaron",
    "bomberos trabajan en", "bomberos acudieron",
]

# Palabras que indican muerte o deceso
FATAL_KEYWORDS = [
    "murió", "falleció", "falló", "perdió la vida", "víctima fatal", "deceso",
    "muerto", "muertos", "muertes", "muerte", "occisos", "occiso", "occisa",
    "no sobrevivió", "sin vida"
]

WIND_MAPPING = {
    # Árboles caídos / viento con daños directos
    "arboles-caidos": [
        "árbol caído", "árbol caido", "arbol caído", "arbol caido",
        "caída de árboles", "caida de arboles", "caída de árbol", "caida de arbol",
        "ramas", "rama caída", "rama caida"
    ],
    # Techos / chapas voladas
    "techo-volado": ["techo", "voladura", "chapa", "volado", "techo voló", "techo volo"],
    # Cortes de energía eléctrica por temporal
    "corte-energia": [
        "corte de luz", "sin luz", "energía san juan", "transformador",
        "cables cortados", "postes caídos", "postes caidos", "sin electricidad",
        "sin energía", "sin energia", "apagón", "apagon"
    ],
    # Granizo
    "granizo": [
        "granizo", "granizos", "granizada", "granizó", "granizo fuerte",
        "caída de granizo", "caida de granizo", "piedras de granizo"
    ],
    # Tormenta eléctrica / rayos
    "tormenta-electrica": [
        "rayo", "rayos", "tormenta eléctrica", "tormenta electrica",
        "relámpago", "relampago", "descarga eléctrica", "descarga electrica",
        "tormenta de rayos"
    ],
    # Inundación urbana
    "inundacion-urbana": [
        "inundación", "inundacion", "inundó", "inundo", "anegó", "anego",
        "anegamiento", "calles inundadas", "barrio inundado", "agua en las calles",
        "agua en calles", "vecinos inundados", "casas inundadas"
    ],
    # Crecida de río
    "creciente-rio": [
        "creciente del río", "creciente del rio", "río creció", "rio crecio",
        "desbordó el río", "desborde del rio", "crecida del río", "crecida del rio",
        "río desbordado", "rio desbordado", "zanjón", "zanjon"
    ],
    # Crecida de quebrada / arroyo
    "creciente-quebrada": [
        "quebrada", "arroyo crecido", "cauce", "cauce desbordado",
        "alud de barro", "barro", "lodo", "aluvión", "aluvion", "alud de lodo"
    ],
    # Corte de ruta por agua
    "corte-ruta-por-agua": [
        "ruta cortada por agua", "ruta anegada", "paso cortado por lluvia",
        "camino cortado", "acceso cortado", "ruta cortada lluvia", "corte de ruta agua"
    ],
    # Derrumbe en ruta
    "derrumbe-ruta": [
        "derrumbe", "derrumbó", "derrumbo", "derrumbe en ruta", "derrumbe ruta",
        "corte de ruta por derrumbe", "ruta bloqueada por derrumbe",
        "desborde de ladera"
    ],
    # Desprendimiento de rocas
    "desprendimiento-rocas": [
        "desprendimiento de rocas", "desprendimiento rocoso", "caída de rocas",
        "caida de rocas", "rodado", "piedras en la ruta", "desprendimiento en sierra",
        "desprendimiento en montaña"
    ],
    # Alud
    "alud": [
        "alud", "avalancha", "deslizamiento", "deslizamiento de tierra",
        "deslizamiento de laderas"
    ],
    # Nevada / helada
    "nevada": [
        "nevada", "nevó", "nevo", "nieve en", "nevadas", "copos de nieve",
        "nieve en la cordillera", "nieve en las sierras", "nieve en san juan"
    ],
    "helada": [
        "helada", "heladas", "temperatura bajo cero", "bajo cero",
        "congelamiento", "escarcha", "hielo en ruta", "ruta helada"
    ],
    # Ola de calor
    "ola-de-calor": [
        "ola de calor", "calor extremo", "temperatura récord", "temperatura record",
        "golpe de calor", "calor sofocante"
    ],
}

ACCIDENT_MAPPING = {
    "choque": ["choque", "chocó", "choco", "chocar", "chocar", "chocaron", "colisión", "colision", "impacto", "impactó", "siniestro vial", "accidente", "vial"],
    "vuelco": ["vuelco", "volcó", "despistó", "cayó", "caída", "caida"],
    "atropello": ["atropelló", "embistió", "peatón", "arrolló", "moto", "motociclista"]
}

FIRE_MAPPING = {
    "incendio-vivienda": ["casa", "vivienda", "departamento", "edificio", "habitación"],
    "incendio-pastizales": ["pastizales", "campo", "lote", "baldío", "maleza"],
    "incendio-vehiculo": ["auto", "camioneta", "camión", "vehículo", "moto", "trafic", "furgón", "furgon", "colectivo"],
    "incendio-forestal": ["bosque", "sierra", "cerro", "montaña", "forestal", "hectáreas", "hectareas"]
}

# Configuración Geográfica (San Juan)
BOUNDING_BOX = [-32.7, -28.2, -70.6, -66.5]

DEPARTAMENTOS = [
    "Capital", "Rawson", "Rivadavia", "Chimbas", "Santa Lucía", 
    "Pocito", "Caucete", "Jáchal", "Albardón", "Sarmiento", 
    "25 de Mayo", "9 de Julio", "San Martín", "Angaco", 
    "Valle Fértil", "Iglesia", "Calingasta", "Ullum", "Zonda"
]

# Configuración de Base de Datos (Ruta absoluta relativa al script para evitar fallos de ejecución)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "database.sqlite")
RULES_PATH = os.path.join(BASE_DIR, "scrapers", "geocoding_rules.json")

# Cargar reglas de geolocalización desde JSON con fallback seguro
try:
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        GEO_RULES = json.load(f)
except Exception as e:
    print(f"[WARNING] No se pudo cargar geocoding_rules.json ({e}). Usando valores por defecto.")
    GEO_RULES = {
        "locality_exclusions": ["cabecera", "san juan"],
        "clean_prefixes": ["^(?:b[°º\\.]|barrio|v[°º\\.]|villa|paraje)\\s+"]
    }

def init_cache_db():
    """
    Inicializa la tabla geocoding_cache y aplica migraciones automáticas
    para agregar columnas nuevas (source, location_type) a bases de datos existentes.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Crear tabla si no existe (esquema completo)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS geocoding_cache (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                query         TEXT    UNIQUE NOT NULL,
                latitude      REAL    NOT NULL,
                longitude     REAL    NOT NULL,
                is_approximate INTEGER NOT NULL,
                source        TEXT    NOT NULL DEFAULT 'nominatim',
                location_type TEXT    NOT NULL DEFAULT 'GEOMETRIC_CENTER',
                created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── Migración automática: agregar columnas si la tabla ya existía sin ellas ──
        existing_cols = {row[1] for row in cursor.execute("PRAGMA table_info(geocoding_cache)")}
        if 'source' not in existing_cols:
            cursor.execute("ALTER TABLE geocoding_cache ADD COLUMN source TEXT NOT NULL DEFAULT 'nominatim'")
            print("[CACHE] Migración: columna 'source' agregada a geocoding_cache.")
        if 'location_type' not in existing_cols:
            cursor.execute("ALTER TABLE geocoding_cache ADD COLUMN location_type TEXT NOT NULL DEFAULT 'GEOMETRIC_CENTER'")
            print("[CACHE] Migración: columna 'location_type' agregada a geocoding_cache.")

        # ── Tabla de hash de contenido: evita re-geocodificar la misma noticia con distinta URL ──
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_hash_cache (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                hash       TEXT    UNIQUE NOT NULL,
                source_url TEXT    NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ERROR] No se pudo inicializar la tabla de caché: {e}")

def get_cached_coords(query, conn=None):
    """
    Consulta si la query ya fue geolocalizada previamente.
    Retorna (latitude, longitude, is_approximate, source, location_type) o None.
    """
    should_close = False
    try:
        if conn is None:
            conn = sqlite3.connect(DB_PATH)
            should_close = True
        cursor = conn.cursor()
        cursor.execute(
            "SELECT latitude, longitude, is_approximate, source, location_type "
            "FROM geocoding_cache WHERE query = ?",
            (query,)
        )
        row = cursor.fetchone()
        if should_close:
            conn.close()
        if row:
            return row[0], row[1], bool(row[2]), row[3], row[4]
    except Exception as e:
        print(f"[ERROR] Error al consultar caché: {e}")
        if should_close and conn:
            try:
                conn.close()
            except Exception:
                pass
    return None

def save_to_cache(query, lat, lon, is_approx, source='google', location_type='GEOMETRIC_CENTER', conn=None):
    """
    Guarda una geolocalización en la caché para evitar futuras consultas de API.
    - source: 'nominatim' | 'google' | 'fallback'
    - location_type: valor de Google ('ROOFTOP', 'RANGE_INTERPOLATED', 'GEOMETRIC_CENTER', 'APPROXIMATE')
                     o 'GEOMETRIC_CENTER' por defecto para resultados de Nominatim.
    """
    should_close = False
    try:
        if conn is None:
            conn = sqlite3.connect(DB_PATH)
            should_close = True
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO geocoding_cache
                (query, latitude, longitude, is_approximate, source, location_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (query, lat, lon, int(is_approx), source, location_type))
        if should_close:
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"[ERROR] Error al guardar en caché: {e}")
        if should_close and conn:
            try:
                conn.close()
            except Exception:
                pass

# Coordenadas estáticas aproximadas (centro geográfico/plaza municipal) para fallback local
DEPARTMENT_COORDINATES = {
    "capital": (-31.5375, -68.5364),
    "rawson": (-31.5471, -68.5262),
    "rivadavia": (-31.5284, -68.5878),
    "chimbas": (-31.4981, -68.5303),
    "santa lucia": (-31.5318, -68.4989),
    "pocito": (-31.6583, -68.5822),
    "caucete": (-31.6519, -68.2744),
    "jachal": (-30.2403, -68.7467),
    "albardon": (-31.4287, -68.5281),
    "sarmiento": (-31.9934, -68.5218),
    "25 de mayo": (-31.8156, -67.9256),
    "9 de julio": (-31.6425, -68.3908),
    "san martin": (-31.4292, -68.2811),
    "angaco": (-31.3925, -68.4239),
    "valle fertil": (-30.6369, -67.4697),
    "iglesia": (-30.2942, -69.1302),
    "calingasta": (-31.2508, -69.4181),
    "ullum": (-31.4194, -68.7303),
    "zonda": (-31.5544, -68.7289)
}

def get_db_fallback_coords(text, conn=None):
    """
    Busca en el texto de la noticia si se menciona algún departamento o localidad.
    Si coincide, consulta en la base de datos y retorna (lat, lon, name_encontrado, tipo)
    usando coordenadas de la DB o el diccionario estático del departamento.
    """
    should_close = False
    try:
        if conn is None:
            conn = sqlite3.connect(DB_PATH)
            should_close = True
        cursor = conn.cursor()
        
        # Cargar los nombres de departamentos en minúsculas para exclusión/clasificación
        cursor.execute("SELECT name FROM departments")
        dept_names_lower = {d[0].lower() for d in cursor.fetchall()}
        
        # 1. Buscar localidades primero (máxima especificidad)
        cursor.execute("""
            SELECT l.name, d.name, l.lat, l.lon 
            FROM localities l
            JOIN departments d ON l.department_id = d.id
        """)
        locs = cursor.fetchall()
        
        # Separar en específicas (ej: Barreal) y genéricas (cuyo nombre coincide con un departamento, ej: Calingasta)
        locs_specific = []
        locs_generic = []
        for row in locs:
            if row[0].lower() in dept_names_lower:
                locs_generic.append(row)
            else:
                locs_specific.append(row)
                
        locs_specific_sorted = sorted(locs_specific, key=lambda x: len(x[0]), reverse=True)
        locs_generic_sorted = sorted(locs_generic, key=lambda x: len(x[0]), reverse=True)
        locs_sorted = locs_specific_sorted + locs_generic_sorted
        
        text_n = normalize_text(text.lower())
        
        for loc_name, dept_name, lat, lon in locs_sorted:
            loc_n = normalize_text(loc_name.lower())
            if len(loc_n) > 4: # evitar palabras muy cortas
                pattern = r'\b' + re.escape(loc_n) + r'\b'
                match_pos = re.search(pattern, text_n)
                if match_pos:
                    # Si la localidad es "Zonda" y está precedida por "viento" o "ráfaga", asumimos que habla del viento
                    if loc_n == "zonda":
                        start_idx = match_pos.start()
                        pre_text = text_n[max(0, start_idx-15):start_idx]
                        if "viento" in pre_text or "rafaga" in pre_text or "rafagas" in pre_text:
                            continue
                            
                    # Si tiene coordenadas explícitas en DB, usarlas
                    if lat is not None and lon is not None:
                        if should_close:
                            conn.close()
                        return float(lat), float(lon), loc_name, 'locality'
                    
                    # Fallback al centro de su departamento correspondiente
                    dept_clean = normalize_text(dept_name.lower())
                    if dept_clean in DEPARTMENT_COORDINATES:
                        d_lat, d_lon = DEPARTMENT_COORDINATES[dept_clean]
                        if should_close:
                            conn.close()
                        return d_lat, d_lon, loc_name, 'locality'
                    
        # 2. Si no hay localidad, buscar departamentos (fallback)
        cursor.execute("SELECT name, lat, lon FROM departments")
        depts = cursor.fetchall()
        for dept_name, lat, lon in depts:
            dept_n = normalize_text(dept_name.lower())
            pattern = r'\b' + re.escape(dept_n) + r'\b'
            match_pos = re.search(pattern, text_n)
            if match_pos:
                # Si el departamento es "Zonda" y está precedida por "viento" o "ráfaga", asumimos que habla del viento
                if dept_n == "zonda":
                    start_idx = match_pos.start()
                    pre_text = text_n[max(0, start_idx-15):start_idx]
                    if "viento" in pre_text or "rafaga" in pre_text or "rafagas" in pre_text:
                        continue
                        
                # Si tiene coordenadas en DB, usarlas
                if lat is not None and lon is not None:
                    if should_close:
                        conn.close()
                    return float(lat), float(lon), dept_name, 'department'
                
                # Fallback al diccionario en memoria
                dept_clean = normalize_text(dept_name.lower())
                if dept_clean in DEPARTMENT_COORDINATES:
                    d_lat, d_lon = DEPARTMENT_COORDINATES[dept_clean]
                    if should_close:
                        conn.close()
                    return d_lat, d_lon, dept_name, 'department'
                
        if should_close:
            conn.close()
    except Exception as e:
        print(f"[FALLBACK-GEO][ERROR] Error buscando coordenadas de fallback: {e}")
        if should_close and conn:
            try:
                conn.close()
            except Exception:
                pass
    return None

def check_incident_precision(url, conn=None):
    """
    Verifica si existe un incidente para esta URL y si su ubicación es aproximada.
    Retorna (exists, is_approximate, old_body)
    """
    should_close = False
    try:
        if conn is None:
            conn = sqlite3.connect(DB_PATH)
            should_close = True
        cursor = conn.cursor()
        
        # Buscar en incidents de Laravel
        cursor.execute("SELECT id, is_approximate FROM incidents WHERE source_url = ?", (url,))
        inc_row = cursor.fetchone()
        
        if not inc_row:
            if should_close:
                conn.close()
            return False, False, None
            
        inc_id, is_approx = inc_row
        
        # Buscar el body_text anterior en raw_articles
        cursor.execute("SELECT body FROM raw_articles WHERE source_url = ?", (url,))
        art_row = cursor.fetchone()
        old_body = art_row[0] if art_row else None
        
        if should_close:
            conn.close()
            
        return True, bool(is_approx), old_body
    except Exception as e:
        print(f"[RE-EVAL][ERROR] Error al verificar precisión del incidente en la DB: {e}")
        if should_close and conn:
            try:
                conn.close()
            except Exception:
                pass
        return False, False, None

# Inicializar caché en el arranque (crea tabla y aplica migraciones)
init_cache_db()

def is_url_processed(url, conn=None):
    """Verifica en la BD local si la URL ya fue ingresada en incidents o raw_articles para evitar raspado redundante"""
    should_close = False
    try:
        if conn is None:
            conn = sqlite3.connect(DB_PATH)
            should_close = True
        cursor = conn.cursor()
        
        # Verificar en incidents
        cursor.execute("SELECT id FROM incidents WHERE source_url = ?", (url,))
        row = cursor.fetchone()
        if row is not None:
            if should_close:
                conn.close()
            return True
            
        # Verificar en raw_articles
        cursor.execute("SELECT id FROM raw_articles WHERE source_url = ?", (url,))
        row = cursor.fetchone()
        if should_close:
            conn.close()
        return row is not None
    except Exception as e:
        print(f"[ERROR] Error al verificar URL duplicada en la DB: {e}")
        if should_close and conn:
            try:
                conn.close()
            except Exception:
                pass
        return False

def save_raw_article(title, description, body_text, source_url, source_name, pub_date_str=None, status='queued', conn=None):
    """Inserta una noticia cruda en la tabla raw_articles de la base de datos SQLite"""
    should_close = False
    try:
        # Formatear la fecha de publicación si existe
        formatted_date = None
        if pub_date_str:
            from email.utils import parsedate_to_datetime
            try:
                dt = parsedate_to_datetime(pub_date_str)
                # Quitar información de zona horaria para compatibilidad SQLite
                dt = dt.replace(tzinfo=None)
                formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
        
        if not formatted_date:
            formatted_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if conn is None:
            conn = sqlite3.connect(DB_PATH)
            should_close = True
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO raw_articles 
                (title, description, body, source_name, source_url, publish_date, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, description, body_text, source_name, source_url, formatted_date, status, now_str, now_str))
        
        # Actualizar el timestamp del último artículo nuevo encontrado para esta fuente
        if status == 'queued':
            try:
                from urllib.parse import urlparse
                parsed_url = urlparse(source_url)
                domain = parsed_url.netloc.replace("www.", "")
                cursor.execute("""
                    UPDATE scraper_sources 
                    SET last_article_at = ? 
                    WHERE domain = ?
                """, (now_str, domain))
            except Exception as domain_err:
                print(f"[MONITOR][ERROR] No se pudo actualizar last_article_at para {source_url}: {domain_err}")

        if should_close:
            conn.commit()
            conn.close()
        print(f"[INGESTA][NUEVO] Guardada en raw_articles ({status}): '{title[:50]}...' ({source_name})")
        return True
    except Exception as e:
        print(f"[INGESTA][ERROR] Error al guardar artículo crudo en la DB: {e}")
        if should_close and conn:
            try:
                conn.close()
            except Exception:
                pass
        return False

def make_content_hash(title: str, pub_date_str: str | None) -> str:
    """
    Genera un hash MD5 del título normalizado + fecha de publicación.
    Detecta la misma noticia publicada con distinta URL (muy común en diarios sanjuaninos).
    """
    normalized = normalize_text(title.strip().lower())
    raw = f"{normalized}|{pub_date_str or ''}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()

def is_content_processed(content_hash: str, conn=None) -> bool:
    """Retorna True si ya procesamos una noticia con este hash de contenido."""
    should_close = False
    try:
        if conn is None:
            conn = sqlite3.connect(DB_PATH)
            should_close = True
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM content_hash_cache WHERE hash = ?", (content_hash,))
        row = cursor.fetchone()
        if should_close:
            conn.close()
        return row is not None
    except Exception as e:
        print(f"[ERROR] Error al verificar hash de contenido: {e}")
        if should_close and conn:
            try:
                conn.close()
            except Exception:
                pass
        return False

def save_content_hash(content_hash: str, source_url: str, conn=None):
    """Persiste el hash de contenido para que futuras corridas no re-geocodifiquen la misma noticia."""
    should_close = False
    try:
        if conn is None:
            conn = sqlite3.connect(DB_PATH)
            should_close = True
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO content_hash_cache (hash, source_url) VALUES (?, ?)",
            (content_hash, source_url)
        )
        if should_close:
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"[ERROR] Error al guardar hash de contenido: {e}")
        if should_close and conn:
            try:
                conn.close()
            except Exception:
                pass

def clean_locality_name(name):
    # Quitar parte después de guión (ej: "Vallecito - Paraje..." -> "Vallecito")
    name_clean = name.split('-')[0].strip()
    # Quitar prefijos comunes usando el patrón del JSON
    for pattern in GEO_RULES.get("clean_prefixes", []):
        name_clean = re.sub(pattern, '', name_clean, flags=re.IGNORECASE)
    return name_clean.strip()

def lookup_locality_in_db(token):
    """
    Consulta la DB en tiempo real para resolver el departamento de un topónimo
    que no fue encontrado en la lista pre-cargada LOCALIDADES_CONTEXT.
    Útil para nombres parciales, variantes de escritura o localidades no normalizadas.
    Retorna 'Localidad, Departamento' si encuentra coincidencia exacta o parcial, o None.
    """
    # Palabras con mayúscula que NO son localidades - evitar falsos positivos en búsqueda parcial
    LOOKUP_EXCLUSIONS = {
        "san", "juan", "santa", "argentina", "buenos", "aires", "córdoba", "cordoba",
        "mendoza", "rosario", "tucumán", "tucuman", "jujuy", "salta", "entre",
        "ríos", "rios", "provincia", "departamento", "barrio", "villa", "calle",
        "avenida", "ruta", "lunes", "martes", "miércoles", "miercoles", "jueves",
        "viernes", "sábado", "sabado", "domingo", "enero", "febrero", "marzo",
        "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
        "noviembre", "diciembre", "hospital", "policía", "policia", "bomberos",
        "nacional", "luján", "lujan", "quilmes", "tigre", "lomas", "norte", "sur"
    }
    if token.lower() in LOOKUP_EXCLUSIONS:
        return None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Búsqueda exacta primero (case-insensitive)
        cursor.execute("""
            SELECT l.name, d.name
            FROM localities l
            JOIN departments d ON l.department_id = d.id
            WHERE LOWER(l.name) = LOWER(?)
            LIMIT 1
        """, (token,))
        row = cursor.fetchone()
        if not row:
            # Búsqueda parcial: el nombre de la localidad contiene el token
            # Solo si el token tiene más de 5 caracteres para evitar matches espurios
            if len(token) > 5:
                cursor.execute("""
                    SELECT l.name, d.name
                    FROM localities l
                    JOIN departments d ON l.department_id = d.id
                    WHERE LOWER(l.name) LIKE LOWER(?)
                    LIMIT 1
                """, (f"%{token}%",))
                row = cursor.fetchone()
        conn.close()
        if row:
            loc_name, dept_name = row
            return f"{loc_name}, {dept_name}"
    except Exception as e:
        print(f"[WARNING] Error en lookup_locality_in_db para '{token}': {e}")
    return None

def load_locations():
    """Carga departamentos y localidades (con su departamento) desde la DB"""
    depts = []
    locs_with_context = {} # Diccionario: 'Talacasto' -> 'Talacasto, Ullum'
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Cargar Departamentos
        cursor.execute("SELECT name FROM departments")
        depts = [row[0] for row in cursor.fetchall()]
        
        # Cargar Localidades con el nombre de su departamento
        cursor.execute("""
            SELECT l.name, d.name 
            FROM localities l 
            JOIN departments d ON l.department_id = d.id
        """)
        for loc_name, dept_name in cursor.fetchall():
            # Exclusión basada en JSON
            should_exclude = False
            for exclusion in GEO_RULES.get("locality_exclusions", []):
                if exclusion.lower() in loc_name.lower():
                    should_exclude = True
                    break
            if should_exclude:
                continue
            
            # Guardar el original
            locs_with_context[loc_name] = f"{loc_name}, {dept_name}"
            
            # Guardar versión limpia (ej: "Media Agua" de "V° Media Agua")
            cleaned_name = clean_locality_name(loc_name)
            
            # Exclusión basada en JSON para nombre limpio
            should_exclude_cleaned = False
            for exclusion in GEO_RULES.get("locality_exclusions", []):
                if exclusion.lower() == cleaned_name.lower():
                    should_exclude_cleaned = True
                    break
                    
            if len(cleaned_name) > 3 and not should_exclude_cleaned and cleaned_name not in locs_with_context:
                locs_with_context[cleaned_name] = f"{cleaned_name}, {dept_name}"
        
        conn.close()
        print(f"[INFO] Ubicaciones cargadas: {len(depts)} departamentos, {len(locs_with_context)} localidades.")
    except Exception as e:
        print(f"[ERROR] No se pudo cargar ubicaciones de la DB: {e}")
        depts = ["Capital", "Rawson", "Rivadavia", "Chimbas", "Santa Lucía", "Pocito", "Caucete", "Jáchal", "Albardón", "Sarmiento", "25 de Mayo", "9 de Julio", "San Martín", "Angaco", "Valle Fértil", "Iglesia", "Calingasta", "Ullum", "Zonda"]
        locs_with_context = {"Talacasto": "Talacasto, Ullum", "Media Agua": "Media Agua, Sarmiento"}
    
    return depts, locs_with_context

DEPARTAMENTOS, LOCALIDADES_CONTEXT = load_locations()
LOCALIDADES = sorted(list(LOCALIDADES_CONTEXT.keys()), key=len, reverse=True)

print(f"[INFO] Scraper iniciado correctamente. Listo para procesar.")

BLACKLIST_PROVINCIAS = ["santa fe", "mendoza", "buenos aires", "córdoba", "cordoba", "san luis", "chile", "nacional", "rosario", "neuquén", "misionero", "corrientes"]

# Frases que indican que el evento ocurrió en OTRO lugar aunque el artículo mencione San Juan
# Formato: "en [ciudad/lugar], [provincia ajena]" o contextos similares
BLACKLIST_EVENT_LOCATION_PATTERNS = [
    r'\ben\s+luj[aá]n\b',                          # en Luján (Bs As)
    r'\ben\s+luj[aá]n,\s*buenos\s+aires\b',
    r'\bcomplejo\s+museogr[aá]fico\b',             # Complejo Museográfico Udaondo
    r'\ben\s+la\s+ciudad\s+de\s+(?:buenos\s+aires|mendoza|c[oó]rdoba|rosario|tucum[aá]n|santa\s+fe)\b',
    r'\ben\s+(?:buenos\s+aires|mendoza|c[oó]rdoba|rosario|tucum[aá]n|santa\s+fe),\b',
    r'\bocurrido\s+en\s+(?!san\s+juan)\w+,\s*(?:buenos\s+aires|mendoza|c[oó]rdoba)\b',
    r'\bucado\s+(?:sobre|en)\s+avenida.*luj[aá]n\b',
]

def clean_location_query(text):
    # Conservar el casing original para que coincidan las mayúsculas de nombres propios
    cleaned = text
    # Eliminar menciones a otras provincias para no confundir al geocoder (case-insensitive)
    for prov in BLACKLIST_PROVINCIAS:
        cleaned = re.sub(re.escape(prov), "", cleaned, flags=re.IGNORECASE)
    # Eliminar palabras que suelen acompañar procedencia (case-insensitive)
    noise = ["de buenos aires", "oriundo de", "proveniente de", "viajaba desde", "hacia", "rumbo a"]
    for word in noise:
        cleaned = re.sub(re.escape(word), "", cleaned, flags=re.IGNORECASE)
    return cleaned

BLACKLIST_KEYWORDS = [
    "internacional", "mundo",
    "escuela", "curso", "capacitación", "capacitacion", "proyecto", "campaña", 
    "historia de", "entrevista", "emicar", "clases", "inscripción", "inscripcion",
    "allanamiento", "detenido", "detenidos", "droga", "estupefacientes", "animales silvestres",
    "fauna", "caza ilegal", "secuestraron armas",
    "obra vial", "obras viales", "obra pública", "obra publica", "obras públicas", "obras publicas",
    "licitación", "licitacion", "licitar", "remodelación", "remodelacion",
    "apertura de sobres", "pavimentación", "pavimentacion", "bacheo", "repavimentación", "repavimentacion",
    "seguridad vial", "educación vial", "educacion vial", "taller de capacitación", "taller de educación", "taller de manejo", "talleres de capacitación", "talleres de educación", "charlas de"
]

PREDICTION_KEYWORDS = [
    "se prevé", "se preve", "prevén", "preven", "se espera", "se pronostica", "pronostican", "es probable", "posibles lluvias",
    "posible granizo", "se anuncia", "anuncian", "podría nevar", "podría llover", "podrian ocurrir",
    "podrían ocurrir", "llegaría", "llegaria", "se anticipa", "se anticipan",
    "alertan por", "alerta por posible", "alerta naranja", "alerta preventiva",
    "alerta amarilla", "alerta roja", "anuncian lluvias", "pronóstico", "pronostico",
    "pronostica lluvias", "pronostica vientos", "pronostica granizo",
    "vientos esperados", "temperaturas previstas", "se espera lluvia",
    "el smn anuncia", "el smn prevé", "el smn alerta", "smn emitió alerta",
    "servicio meteorológico", "meteorológico nacional",
    "guardia de incendios previene", "recomiendan no salir",
    "prevención por vientos", "prevención por granizo", "precaución para transitar",
    "se recomienda no encender", "no quemar en días de viento",
    "evitar circular ante", "alerta por viento", "alerta por tormenta",
    "alerta por zonda", "alerta de viento", "alerta por temporal", "alerta de temporal"
]

INCIDENT_CONFIRMED_KEYWORDS = [
    "cayó", "cayo", "derribó", "derribo", "voló", "volo",
    "se desbordó", "se desbordo", "inundó", "inundo",
    "se cortó", "se corto", "quedó cortada", "quedo cortada",
    "ardieron", "ardió", "ardio", "combaten", "combatieron",
    "evacuaron", "evacuó", "evacuo", "evacuados", "evacuadas",
    "nevó", "nevo", "granizó", "granizo",
    "hubo fuertes", "registraron", "se registraron",
    "resultaron", "ocasionó", "ocasiono", "provocó", "provoco",
    "dejó sin", "dejo sin", "volaron techos", "postes caídos",
    "ruta cortada", "paso cerrado", "calles anegadas",
    "incendio", "incendios", "fuego", "ramas caídas", "ramas caidas", "árbol caído", "árbol caido",
    "corte de luz", "sin luz", "asistieron", "asistió", "asistio", "asistencia", "asistidas",
    "asistidos", "asistido", "desmovilizó", "desmovilizaron", "desmovilizo",
    "cubrió", "cubrio", "cubiertos", "cubiertas", "sepultó", "sepulto", "sepultados", "sepultadas",
    "acumuló", "acumulo", "acumulación", "acumulaciones", "temporal", "temporales", "nevada", "nevadas"
]


MEDIA_NAMES = {
    "diariodecuyo.com.ar": "Diario de Cuyo",
    "tiempodesanjuan.com": "Tiempo de San Juan",
    "diariohuarpe.com": "Diario Huarpe",
    "nuevodiariosanjuan.com.ar": "Nuevo Diario",
    "diariomovil.info": "Diario Móvil",
    "diarioelzonda.com.ar": "Diario El Zonda",
    "sanjuan8.com": "San Juan 8",
    "diariolaprovinciasj.com": "Diario La Provincia",
    "canal4sanjuan.com.ar": "Canal 4 San Juan",
    "canal13sanjuan.com": "Diario 13 San Juan",
    "nuevomundosj.com.ar": "Nuevo Mundo",
    "telesoldiario.com": "Telesol Diario"
}


def is_within_bounds(lat, lon):
    return BOUNDING_BOX[0] <= lat <= BOUNDING_BOX[1] and BOUNDING_BOX[2] <= lon <= BOUNDING_BOX[3]

def extract_location_with_gemini(title, description, body_text):
    """
    Analiza la noticia con Gemini 2.5 Flash y extrae información estructurada:
    location_query, is_approximate, is_fatal, category, wind_cause, phenomenon_type, hectares_burned.
    """
    gemini_key = get_env_variable("GEMINI_API_KEY")
    if not gemini_key:
        return None

    global gemini_calls_in_run
    max_calls = int(get_env_variable("MAX_GEMINI_CALLS_PER_RUN", "30"))
    if gemini_calls_in_run >= max_calls:
        print(f"[GEMINI][LIMIT] Se alcanzó el límite de {max_calls} llamadas por ciclo. Omitiendo Gemini para esta noticia.")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = f"""Analiza la siguiente noticia de la provincia de San Juan, Argentina, y extrae la información solicitada de forma estructurada.

**Instrucción de Desambiguación Crítica para 'Zonda'**:
- La palabra 'Zonda' puede referirse al viento ("viento Zonda", "ráfagas de Zonda", "Zonda activo") o al departamento/localidad ("en Zonda", "en el departamento Zonda", "vecinos de Zonda").
- Si se refiere al viento Zonda, clasifícalo en `wind_cause = true` y selecciona la categoría climática correspondiente (por ejemplo: `arboles-caidos`, `techo-volado`, `corte-energia`, `incendio-pastizales`, etc.) y asigna `zonda` en `phenomenon_type`.
- Si se menciona Zonda como el lugar geográfico del hecho, devuélvelo en `location_query` como 'Zonda, San Juan, Argentina' o el lugar específico dentro del departamento, pero no actives `wind_cause` a menos que también se mencione el viento Zonda como causa del incidente.

**Instrucción para Proyectos Mineros Cordilleranos**:
- En la provincia de San Juan existen importantes proyectos mineros y de exploración en alta montaña donde ocurren tormentas de nieve, vientos fuertes y evacuaciones. Si la noticia refiere a un incidente en un proyecto minero o yacimiento (ej: Veladero, Gualcamayo, Casposo, Manantiales, Josemaría, Los Azules, El Pachón, Altar, Filo del Sol, Hualilán, Vicuña, Lama, Chinchillas, San Francisco), extrae su ubicación exacta. Devuelve 'location_query' en el formato: 'Mina [Nombre Proyecto], [Departamento], San Juan, Argentina' (ej: 'Mina Los Azules, Calingasta, San Juan, Argentina' o 'Mina Veladero, Iglesia, San Juan, Argentina').

**IMPORTANTE — Solo Incidentes Reales, No Predicciones**:
- Solo debes clasificar la noticia si reporta un incidente o fenómeno climático que ya ocurrió en el pasado o presente inmediato (ej: "cayeron árboles", "se cortó la ruta", "nevó", "se registraron incendios", "volaron techos").
- Si la noticia es puramente preventiva, habla de una predicción meteorológica futura, una alerta preventiva sin reportar hechos sucedidos, o recomendaciones de organismos públicos para el futuro (ej: "se prevé viento", "es probable que granice", "alertan por zonda", "recomiendan no salir"), debes devolver `is_retrospective_or_historical = true` para indicarle al sistema que la descarte.

Título: {title}
Descripción: {description}
Cuerpo: {body_text}"""

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "location_query": {
                        "type": "STRING",
                        "description": "Una consulta de dirección limpia y específica en San Juan, Argentina. Ej: 'Avenida Libertador & San Miguel' o 'Ruta 40 y Calle 9' o 'Hospital Rawson'. Si solo se menciona un departamento general sin calles ni referencias de altura, devolver el nombre del departamento/localidad."
                    },
                    "is_approximate": {
                        "type": "BOOLEAN",
                        "description": "true si la dirección es aproximada (solo se conoce el departamento, localidad o barrio general sin calles específicas). false si la dirección es exacta (se menciona una calle y altura, intersección de calles, o un lugar muy específico como un hospital o plaza)."
                    },
                    "is_fatal": {
                        "type": "BOOLEAN",
                        "description": "true si la noticia indica claramente que hubo al menos una víctima fatal o fallecido en el lugar. false en caso contrario."
                    },
                    "category": {
                        "type": "STRING",
                        "enum": [
                            "arboles-caidos", "techo-volado", "corte-energia",
                            "incendio-pastizales", "incendio-forestal", "incendio-vivienda", "incendio-vehiculo",
                            "granizo", "tormenta-electrica", "inundacion-urbana",
                            "creciente-rio", "creciente-quebrada", "corte-ruta-por-agua",
                            "derrumbe-ruta", "desprendimiento-rocas", "alud",
                            "nevada", "helada", "ola-de-calor", "accidente-climatico",
                            "otro-climatico", "desconocido"
                        ],
                        "description": "La categoría del incidente."
                    },
                    "wind_cause": {
                        "type": "BOOLEAN",
                        "description": "true si el viento (sea Zonda o Sur o ráfagas fuertes) causó el incidente. false en caso contrario."
                    },
                    "phenomenon_type": {
                        "type": "STRING",
                        "enum": ["zonda", "viento_sur", "tormenta", "creciente", "derrumbe", "otro_climatico", "ninguno"],
                        "description": "El tipo de fenómeno climático asociado al incidente. Ej: 'zonda' si es viento zonda, 'viento_sur' si es viento sur, 'tormenta' si es lluvia/granizo/tormenta, 'creciente' si es crecida de río/arroyo/quebrada, 'derrumbe' si es desprendimiento de rocas/alud/derrumbe en ruta, 'otro_climatico' para otros."
                    },
                    "hectares_burned": {
                        "type": "NUMBER",
                        "description": "La cantidad de hectáreas quemadas si la noticia refiere a un incendio forestal o de pastizales y menciona explícitamente el número de hectáreas. Si no se especifica o no aplica, devolver -1."
                    },
                    "is_retrospective_or_historical": {
                        "type": "BOOLEAN",
                        "description": "true si la noticia es una retrospectiva, un aniversario, un recuento histórico, actualizaciones o sentencias judiciales de un caso antiguo, o habla de un hecho que ocurrió hace meses o años. false si reporta un suceso vial, incendio o caída de ramas/árboles reciente que ocurrió en los últimos días."
                    },
                    "victim_names": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "Nombres propios completos de las víctimas o personas físicas involucradas mencionadas en la noticia (ej: 'Juan Pérez'). No incluir nombres de policías, médicos, jueces o fiscales. Devolver array vacío si no hay nombres."
                    },
                    "has_car": {
                        "type": "BOOLEAN",
                        "description": "true si un auto, automóvil, taxi, remis o coche estuvo involucrado en el hecho."
                    },
                    "has_pickup": {
                        "type": "BOOLEAN",
                        "description": "true si una camioneta o pick-up (ej: Hilux, Amarok, Ranger) estuvo involucrada."
                    },
                    "has_utility": {
                        "type": "BOOLEAN",
                        "description": "true si un utilitario o furgón (ej: Kangoo, Fiorino, Partner, Trafic) estuvo involucrado."
                    },
                    "has_motorcycle": {
                        "type": "BOOLEAN",
                        "description": "true si una motocicleta, moto o ciclomotor estuvo involucrado."
                    },
                    "has_truck": {
                        "type": "BOOLEAN",
                        "description": "true si un camión, acoplado o semirremolque estuvo involucrado."
                    },
                    "has_bus": {
                        "type": "BOOLEAN",
                        "description": "true si un colectivo, ómnibus o micro de pasajeros estuvo involucrado."
                    },
                    "has_pedestrian": {
                        "type": "BOOLEAN",
                        "description": "true si un peatón o transeúnte fue atropellado o involucrado."
                    },
                    "has_bicycle": {
                        "type": "BOOLEAN",
                        "description": "true si una bicicleta o ciclista estuvo involucrado."
                    }
                },
                "required": [
                    "location_query", "is_approximate", "is_fatal", "category", 
                    "wind_cause", "phenomenon_type", "hectares_burned",
                    "is_retrospective_or_historical", "victim_names",
                    "has_car", "has_pickup", "has_utility", "has_motorcycle", 
                    "has_truck", "has_bus", "has_pedestrian", "has_bicycle"
                ]
            }
        }
    }

    try:
        print(f"[GEMINI] Analizando noticia: '{title[:60]}...'")
        response = requests.post(url, headers=headers, json=payload, timeout=12)
        if response.status_code == 200:
            gemini_calls_in_run += 1
            data = response.json()
            text = data['candidates'][0]['content']['parts'][0]['text'].strip()
            result = json.loads(text)
            
            # Obtener uso de tokens de los metadatos de respuesta de Google
            usage = data.get("usageMetadata", {})
            prompt_tokens = usage.get("promptTokenCount", 0)
            candidates_tokens = usage.get("candidatesTokenCount", 0)
            total_tokens = usage.get("totalTokenCount", 0)
            
            print(f"[GEMINI] Éxito (Tokens: In={prompt_tokens}, Out={candidates_tokens}, Total={total_tokens}). Extracción: {result}")
            return result
        else:
            print(f"[GEMINI][WARNING] HTTP {response.status_code} al consultar Gemini: {response.text}")
    except Exception as e:
        print(f"[GEMINI][ERROR] Excepción al consultar Gemini: {e}")
    
    return None

def resolve_geocode_google(query_str):
    """
    Geocodifica usando Google Geocoding API como fallback de Nominatim.
    - Aplica Component Restriction: solo devuelve resultados en San Juan, Argentina.
    - Captura location_type para determinar precisión:
        ROOFTOP            → exacto (edificio/domicilio)
        RANGE_INTERPOLATED → preciso (punto en cuadra)
        GEOMETRIC_CENTER   → aproximado (centro de calle o barrio)
        APPROXIMATE        → muy aproximado (ciudad o zona)
    Retorna (lat, lon, is_approximate, location_type, formatted_address) o None.
    """
    api_key = get_env_variable("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return None

    global google_maps_calls_in_run
    max_calls = int(get_env_variable("MAX_GOOGLE_MAPS_CALLS_PER_RUN", "30"))
    if google_maps_calls_in_run >= max_calls:
        print(f"[GOOGLE][LIMIT] Se alcanzó el límite de {max_calls} llamadas por ciclo. Omitiendo Google Maps para esta noticia.")
        return None

    print(f"[GOOGLE] Consultando geocoding para: '{query_str}'")
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": query_str,
            "components": "administrative_area:San Juan|country:AR",
            "region": "ar",   # Prioriza resultados de Argentina globalmente
            "key": api_key
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")

            if status == "OK" and data.get("results"):
                google_maps_calls_in_run += 1
                result = data["results"][0]
                geometry = result.get("geometry", {})
                location = geometry.get("location", {})
                lat = location.get("lat")
                lng = location.get("lng")

                # ROOFTOP y RANGE_INTERPOLATED son suficientemente precisos.
                # GEOMETRIC_CENTER y APPROXIMATE se consideran aproximados.
                loc_type = geometry.get("location_type", "APPROXIMATE")
                is_approx = loc_type not in ("ROOFTOP", "RANGE_INTERPOLATED")
                formatted = result.get("formatted_address", "")

                if lat and lng and is_within_bounds(lat, lng):
                    print(f"[GOOGLE] OK - {formatted} ({loc_type}) -> {lat}, {lng}")
                    return lat, lng, is_approx, loc_type, formatted
                else:
                    print(f"[GOOGLE][WARNING] Coords fuera de bounding box para '{query_str}': {lat}, {lng}")

            elif status == "ZERO_RESULTS":
                print(f"[GOOGLE] Sin resultados para: '{query_str}'")
            else:
                print(f"[GOOGLE][WARNING] Status inesperado '{status}' para: '{query_str}'")
        else:
            print(f"[GOOGLE][WARNING] HTTP {response.status_code} para: '{query_str}'")

    except Exception as e:
        print(f"[GOOGLE][ERROR] Excepción consultando '{query_str}': {e}")

    return None

def resolve_geocode(query_str, is_approx, conn=None):
    """
    Resuelve una geolocalización con el máximo de precisión posible.
    Embudo de 2 niveles (diseño simplificado para volúmenes bajos con alta calidad):

      1. Caché SQLite  → hit instantáneo, sin costo.
      2. Google Geocoding API → máxima precisión para Argentina.
         (40.000 consultas/mes gratuitas — más que suficiente para este proyecto)

    Nominatim fue descartado porque produce ubicaciones incorrectas en direcciones
    argentinas (ej. esquinas de San Juan devueltas a localidades equivocadas).

    Retorna (latitude, longitude, is_approximate, source, location_type) o None.
    """
    # 1. Caché local → hit instantáneo, costo cero
    cached = get_cached_coords(query_str, conn=conn)
    if cached is not None:
        lat, lon, approx, source, loc_type = cached
        print(f"[CACHE] HIT ({source} / {loc_type}): '{query_str}'")
        return lat, lon, approx, source, loc_type

    # 2. Google Geocoding API → precisión máxima, restricción a San Juan, AR
    google_res = resolve_geocode_google(query_str)
    if google_res:
        g_lat, g_lng, g_approx, g_loc_type, g_formatted = google_res
        final_approx = g_approx or is_approx
        save_to_cache(
            query_str, g_lat, g_lng, final_approx,
            source='google', location_type=g_loc_type, conn=conn
        )
        return g_lat, g_lng, final_approx, 'google', g_loc_type

    print(f"[GEO][FALLO] No se pudo resolver: '{query_str}'")
    return None


def sanitize_location_text(text, rule=None):
    """Limpia el texto de falsos positivos basándose en las reglas del JSON"""
    cleaned = text
    if rule and rule.get("sanitize_exclusions"):
        for exclusion in rule["sanitize_exclusions"]:
            if "hospital rawson" in exclusion.lower():
                cleaned = re.sub(r'hospital(?:\s+dr\.?)?(?:\s+guillermo)?\s+rawson', '', cleaned, flags=re.IGNORECASE)
            else:
                cleaned = re.sub(r'\b' + re.escape(exclusion) + r'\b', '', cleaned, flags=re.IGNORECASE)
    else:
        # Fallback default
        cleaned = re.sub(r'hospital(?:\s+dr\.?)?(?:\s+guillermo)?\s+rawson', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'hospital\s+rawson', '', cleaned, flags=re.IGNORECASE)
    return cleaned

def _is_used_as_street_name(name, text):
    """
    Verifica si un nombre geográfico (departamento/localidad) está siendo usado
    como nombre de calle/avenida/ruta en el texto (ej: "calle Sarmiento", "Av. Rawson").
    Si está precedido por un prefijo vial, NO debe usarse como contexto geográfico.
    """
    # Prefijos viales que indican que el nombre es una calle, no una zona geográfica
    street_prefixes = r'(?:[Cc]alle[s]?\s+|[Aa]v(?:enida)?\.?\s+|[Rr]uta\s+)'
    pattern = street_prefixes + re.escape(name) + r'\b'
    return bool(re.search(pattern, text, re.IGNORECASE))

def _has_non_street_occurrence(name, text):
    """
    Verifica si el nombre aparece en el texto en un contexto que NO sea de calle.
    Por ejemplo, "en Albardón" o "ocurrió en Sarmiento" (sin prefijo vial).
    Retorna True si hay al menos una ocurrencia que no sea nombre de calle.
    """
    # Buscar todas las ocurrencias del nombre
    all_matches = list(re.finditer(r'\b' + re.escape(name) + r'\b', text, re.IGNORECASE))
    if not all_matches:
        return False
    
    street_prefixes = r'(?:[Cc]alle[s]?\s+|[Aa]v(?:enida)?\.?\s+|[Rr]uta\s+)'
    for m in all_matches:
        # Tomar un fragmento antes del match para verificar si tiene prefijo vial
        start = max(0, m.start() - 20)
        preceding = text[start:m.start()]
        if not re.search(street_prefixes + r'$', preceding, re.IGNORECASE):
            return True  # Esta ocurrencia NO es nombre de calle
    
    return False  # Todas las ocurrencias son nombres de calle

def get_hierarchical_context(text, rule=None):
    """
    Busca contexto siguiendo la prioridad: Localidad -> Departamento -> Provincia
    Ignora nombres que aparecen exclusivamente como nombres de calle/avenida/ruta
    (ej: "calle Sarmiento" no debe interpretarse como departamento Sarmiento).
    """
    text = sanitize_location_text(text, rule)
    # 1. Prioridad: Localidad (Máxima precisión con su departamento)
    for loc in LOCALIDADES:
        pattern = r'\b' + re.escape(loc) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            # Evitar colisión si el nombre de la localidad coincide con un departamento
            # (ej: "Sarmiento" de "Villa Sarmiento", "San Martín" de "Villa San Martín")
            is_collision = False
            for dept in DEPARTAMENTOS:
                if loc.lower() == dept.lower():
                    is_collision = True
                    break
            
            if is_collision:
                # Exigir que la frase completa de la localidad (o versiones con villa/barrio)
                # esté en el texto para diferenciarlo del departamento homónimo.
                full_names_to_check = [f"villa {loc.lower()}", f"b° {loc.lower()}", f"barrio {loc.lower()}"]
                if not any(fn in text.lower() for fn in full_names_to_check):
                    continue
            
            # Si este nombre SOLO aparece como nombre de calle, no usarlo como contexto
            if _is_used_as_street_name(loc, text) and not _has_non_street_occurrence(loc, text):
                continue
            
            return f"{LOCALIDADES_CONTEXT[loc]}, San Juan, Argentina"

    # 2. Prioridad: Departamento
    for dept in DEPARTAMENTOS:
        pattern = r'\b' + re.escape(dept) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            # Si este nombre SOLO aparece como nombre de calle, no usarlo como contexto
            if _is_used_as_street_name(dept, text) and not _has_non_street_occurrence(dept, text):
                continue
            return f"{dept}, San Juan, Argentina"

    # 3. Fallback dinámico: buscar en la DB si hay algún token del texto que coincida
    # con una localidad no pre-cargada (variantes de escritura, nombres parciales, etc.)
    tokens = re.findall(r'[A-ZÁÉÍÓÚ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚ][a-záéíóúñ]+)*', text)
    for token in tokens:
        if len(token) < 4:
            continue
        # Si este token SOLO aparece como nombre de calle, no usarlo como contexto
        if _is_used_as_street_name(token, text) and not _has_non_street_occurrence(token, text):
            continue
        db_result = lookup_locality_in_db(token)
        if db_result:
            print(f"[GEO-DB] Localidad resuelta desde DB: '{token}' -> '{db_result}'")
            return f"{db_result}, San Juan, Argentina"

    fallback = rule.get("fallback_context", "San Juan, Argentina") if rule else "San Juan, Argentina"
    return fallback

def geocoding_funnel(text, rule=None):
    # Limpiar el texto de ruidos geográficos (Buenos Aires, etc) antes de buscar patrones
    text_sanitized = sanitize_location_text(text, rule)
    text_clean = clean_location_query(text_sanitized)
    local_context = get_hierarchical_context(text_sanitized, rule)
    
    # 1. Caso especial: Ruta y Calle numérica (ej. Ruta 40 y Calle 9 o Calles 9 y 10)
    ruta_match = re.search(r"([Rr]uta\s+\d+)", text_clean, re.IGNORECASE)
    calle_num_match = re.search(r"(?:[Cc]alle[s]?)\s+(\d+)", text_clean, re.IGNORECASE)
    if ruta_match and calle_num_match:
        ruta = ruta_match.group(1)
        calle_num = calle_num_match.group(1)
        query = f"{ruta} & Calle {calle_num}, {local_context}"
        coords = resolve_geocode(query, False)
        if coords:
            return coords[0], coords[1], False, coords[3], coords[4]

    # 2. Caso especial: Intersección de calle numérica y otra calle numérica (ej. Calle 9 y 10)
    calle_num_interseccion = re.search(r"[Cc]alle[s]?\s+(\d+)\s+(?:y|e|entre)\s+(\d+)", text_clean, re.IGNORECASE)
    if calle_num_interseccion:
        c1 = calle_num_interseccion.group(1)
        c2 = calle_num_interseccion.group(2)
        query = f"Calle {c1} & Calle {c2}, {local_context}"
        coords = resolve_geocode(query, False)
        if coords:
            return coords[0], coords[1], False, coords[3], coords[4]

    intersection_patterns = [
        # Ruta X y Calle Nombre (ej. Ruta 40 y Agustín Gómez)
        r"([Rr]uta\s+\d+)\s+(?:y|e|esquina|intersección\s+con|a\s+la\s+altura\s+de|frente\s+al)\s*(?:[Cc]alle[s]?|[Aa]v\.?|[Aa]venida|[Rr]uta)?\s*([A-ZÁÉÍÓÚ][a-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-zñáéíóú]+)*)",
        # Calle Nombre y Ruta X (ej. Agustín Gómez y Ruta 40)
        r"(?:[Cc]alle[s]?|[Aa]v\.?|[Aa]venida)?\s*([A-ZÁÉÍÓÚ][a-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-zñáéíóú]+)*)\s*(?:y|e|esquina|intersección\s+con)\s*([Rr]uta\s+\d+)",
        # Calle Nombre y Calle Nombre
        r"(?:[Cc]alle[s]?|[Aa]v\.?|[Aa]venida|[Rr]uta)?\s*([A-ZÁÉÍÓÚ][a-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-zñáéíóú]+)*)\s*(?:y|e|esquina|intersección\s+con|a\s+la\s+altura\s+de|frente\s+al)\s*(?:[Cc]alle[s]?|[Aa]v\.?|[Aa]venida|[Rr]uta)?\s*([A-ZÁÉÍÓÚ][a-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-zñáéíóú]+)*)"
    ]
    
    linear_precise_patterns = [
        # Ruta X Km Y
        r"([Rr]uta\s+\d+)\s+(?:[Kk]m\.?|[Kk]il[óo]metro)\s+(\d+)",
        # Calle Nombre al X (altura)
        r"([Cc]alle[s]?|[Aa]v\.?|[Aa]venida|[Rr]uta)\s+([A-ZÁÉÍÓÚ][a-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-zñáéíóú]+)*)\s+(?:al|altura)\s+(\d+)"
    ]
    
    approximate_patterns = [
        r"([Rr]uta\s+\d+)",
        r"([Aa]eropuerto|[Tt]erminal|[Cc]entro|[Pp]laza|[Bb]arrio|[Vv]illa)\s+([A-ZÁÉÍÓÚ][a-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-zñáéíóú]+)*)"
    ]
    
    for pattern in intersection_patterns:
        match = re.search(pattern, text_clean)
        if match:
            query = " & ".join(filter(None, match.groups()))
            coords = resolve_geocode(f"{query}, {local_context}", False)
            if coords:
                return coords[0], coords[1], False, coords[3], coords[4]
            fallback = rule.get("fallback_context", "San Juan, Argentina") if rule else "San Juan, Argentina"
            if local_context != fallback:
                coords_fallback = resolve_geocode(f"{query}, {fallback}", False)
                if coords_fallback:
                    return coords_fallback[0], coords_fallback[1], False, coords_fallback[3], coords_fallback[4]

    for pattern in linear_precise_patterns:
        match = re.search(pattern, text_clean)
        if match:
            query = " ".join(filter(None, match.groups()))
            coords = resolve_geocode(f"{query}, {local_context}", False)
            if coords:
                return coords[0], coords[1], False, coords[3], coords[4]
            fallback = rule.get("fallback_context", "San Juan, Argentina") if rule else "San Juan, Argentina"
            if local_context != fallback:
                coords_fallback = resolve_geocode(f"{query}, {fallback}", False)
                if coords_fallback:
                    return coords_fallback[0], coords_fallback[1], False, coords_fallback[3], coords_fallback[4]

    for pattern in approximate_patterns:
        match = re.search(pattern, text_clean)
        if match:
            query = " ".join(filter(None, match.groups()))
            coords = resolve_geocode(f"{query}, {local_context}", True)
            if coords:
                return coords[0], coords[1], True, coords[3], coords[4]

    for loc in LOCALIDADES:
        pattern = r'\b' + re.escape(loc.lower()) + r'\b'
        if re.search(pattern, text.lower()):
            # Evitar colisión si el nombre de la localidad coincide con un departamento
            is_collision = False
            for dept in DEPARTAMENTOS:
                if loc.lower() == dept.lower():
                    is_collision = True
                    break
            
            if is_collision:
                full_names_to_check = [f"villa {loc.lower()}", f"b° {loc.lower()}", f"barrio {loc.lower()}"]
                if not any(fn in text.lower() for fn in full_names_to_check):
                    continue
            
            coords = resolve_geocode(f"{LOCALIDADES_CONTEXT[loc]}, San Juan, Argentina", True)
            if coords:
                return coords[0], coords[1], True, coords[3], coords[4]

    for dept in DEPARTAMENTOS:
        pattern = r'\b' + re.escape(dept.lower()) + r'\b'
        if re.search(pattern, text.lower()):
            coords = resolve_geocode(f"{dept}, San Juan, Argentina", True)
            if coords:
                return coords[0], coords[1], True, coords[3], coords[4]

    if any(re.search(r'\b' + re.escape(loc.lower()) + r'\b', text.lower()) for loc in LOCALIDADES) or \
       any(re.search(r'\b' + re.escape(dept.lower()) + r'\b', text.lower()) for dept in DEPARTAMENTOS) or \
       re.search(r'\bsan juan\b', text.lower()):
        return -31.5375, -68.53639, True, 'fallback', 'APPROXIMATE'
    return None

def clean_html(text):
    if not text:
        return ""
    # Eliminar etiquetas HTML completas (como <img ... />, <a ...>, etc.)
    cleaned = re.sub(r'<[^>]+>', '', text)
    # Reemplazar entidades HTML comunes (como &amp;, &quot;, &#39;)
    cleaned = html.unescape(cleaned)
    # Colapsar espacios y saltos de línea adicionales
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def has_keyword_match(text, keyword):
    """
    Verifica si una palabra clave está en el texto de forma precisa.
    - Normaliza tildes y diacríticos (e.g. 'arbol' == 'árbol').
    - Si la keyword tiene espacios (ej. "siniestro vial"), realiza coincidencia de subcadena.
    - Si es una palabra única (ej. "impacto", "choque"), exige límites de palabra (\b)
      para evitar falsos positivos (como "impacto" coincidiendo dentro de "impactos").
    """
    text_n = normalize_text(text)
    kw_n = normalize_text(keyword)
    if ' ' in kw_n:
        return kw_n in text_n
    return bool(re.search(r'\b' + re.escape(kw_n) + r'\b', text_n))


def fetch_article_text(url):
    """Descarga el cuerpo de la noticia y extrae el texto de las etiquetas de párrafo, filtrando navegación/pie de página"""
    try:
        print(f"[DEEP FETCH] Buscando detalles en la URL: {url}")
        response = requests.get(url, headers=get_headers(url), timeout=10, verify=False)
        if response.status_code == 200:
            html_content = response.text
            
            # Limpiar cabeceras, menús, pies de página, barras laterales y de navegación para evitar falsos positivos
            # de palabras clave (como 'tránsito', 'automotores', 'secciones') en la publicidad o el menú
            html_clean = html_content
            html_clean = re.sub(r'<header[^>]*>.*?</header>', '', html_clean, flags=re.DOTALL | re.IGNORECASE)
            html_clean = re.sub(r'<footer[^>]*>.*?</footer>', '', html_clean, flags=re.DOTALL | re.IGNORECASE)
            html_clean = re.sub(r'<nav[^>]*>.*?</nav>', '', html_clean, flags=re.DOTALL | re.IGNORECASE)
            html_clean = re.sub(r'<aside[^>]*>.*?</aside>', '', html_clean, flags=re.DOTALL | re.IGNORECASE)
            
            # Eliminar contenedores comunes de barras laterales, comentarios, redes sociales, etc.
            html_clean = re.sub(r'<div[^>]*(?:class|id)="[^"]*(?:sidebar|menu|nav|aside|header|footer|comments|social|share|relacionad|destacad)[^"]*"[^>]*>.*?</div>', '', html_clean, flags=re.DOTALL | re.IGNORECASE)
            
            content_parts = []
            # Meta description
            meta_desc = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html_content, re.IGNORECASE)
            if meta_desc: content_parts.append(clean_html(meta_desc.group(1)))

            # Copetes / Subtítulos
            copete_matches = re.findall(r'<(?:div|p|h2)[^>]*class=["\'](?:noticia-copete|noticia-description|article-description|subtitulo|copete|lead)[^"\']*["\'][^>]*>(.*?)</(?:div|p|h2)>', html_clean, re.DOTALL | re.IGNORECASE)
            for c in copete_matches: content_parts.append(clean_html(c))

            # Párrafos
            p_matches = re.findall(r'<p[^>]*>(.*?)</p>', html_clean, re.DOTALL)
            for p in p_matches:
                p_clean = clean_html(p)
                if len(p_clean) > 30 and not any(x in p_clean.lower() for x in ["copyright", "todos los derechos", "comercial:", "términos y condiciones"]):
                    content_parts.append(p_clean)

            return "\n".join(content_parts)
    except Exception as e:
        print(f"[WARNING] No se pudo obtener el cuerpo del artículo desde {url}: {e}")
    return ""


def is_blacklisted(text, blacklist_list):
    """Verifica si el texto contiene palabras de la lista negra respetando límites de palabra para términos simples."""
    text_n = normalize_text(text)
    for kw in blacklist_list:
        kw_n = normalize_text(kw)
        if ' ' in kw_n:
            if kw_n in text_n:
                return True
        else:
            if bool(re.search(r'\b' + re.escape(kw_n) + r'\b', text_n)):
                return True
    return False

def classify_article_with_python_rules(title, description, body_text, rule=None):
    """
    Clasifica una noticia utilizando las reglas tradicionales de Python (palabras clave y exclusiones).
    Retorna la categoría detectada (slug) o None si no corresponde a un incidente válido.
    """
    title_desc_combined = (title + " " + (description or "")).lower()
    text_to_search = (title + " " + (description or "") + " " + (body_text or "")).lower()
    
    # Ruidos y falsos positivos de "fuego" / "impacto" / "giro"
    text_to_search = text_to_search.replace("matafuegos", "").replace("matafuego", "")
    for term in [
        "fuerte impacto", "gran impacto", "alto impacto", "bajo impacto", 
        "impacto economico", "impacto social", "impacto politico", "impacto ambiental",
        "impacto de la noticia", "causo impacto", "genero impacto", "provoco impacto",
        "dieron un giro", "giro inesperado", "giro en la investigacion", "giro en la causa"
    ]:
        text_to_search = text_to_search.replace(term, "")
        title_desc_combined = title_desc_combined.replace(term, "")

    # 1. Filtros de palabras prohibidas globales
    has_blacklist = is_blacklisted(text_to_search, BLACKLIST_KEYWORDS)
    if has_blacklist:
        # Excepción: Si contiene una confirmación clara de incidente climático/incendio real,
        # permitimos que pase a pesar de contener términos policiales como "detenido" o "detenidos".
        is_strong_climate = any(kw in text_to_search for kw in ["incendio", "incendios", "fuego", "viento zonda", "temporal", "nieve", "nevada", "nevadas", "inundacion", "crecida", "derrumbe", "arboles caidos", "caida de arboles"])
        if not is_strong_climate:
            return None
        # Si es climático pero contiene ruidos no deseados irremediables (ej. capacitaciones, cursos), descartamos
        always_ignore = ["curso", "capacitación", "capacitacion", "taller de capacitación", "taller de educación", "taller de manejo", "charlas de", "inscripción", "inscripcion", "proyecto de ley", "proyecto de resolucion", "proyecto legislativo", "proyecto de ordenanza", "campaña"]
        if is_blacklisted(text_to_search, always_ignore):
            return None

    if rule and rule.get("ignore_terms"):
        if is_blacklisted(text_to_search, rule["ignore_terms"]):
            return None

    # 1b. Filtrar predicciones / alertas preventivas (no son incidentes reales)
    is_prediction = any(kw in text_to_search for kw in PREDICTION_KEYWORDS)
    has_confirmed_incident = any(kw in text_to_search for kw in INCIDENT_CONFIRMED_KEYWORDS)
    if is_prediction and not has_confirmed_incident:
        print(f"[RULES][PREDICTION-SKIP] Noticia es predicción/alerta preventiva (omitida): '{title[:60]}...'")
        return None

    # 2. Filtrado de provincias (exclusión de noticias fuera de San Juan)
    mentions_other_province = any(prov in text_to_search for prov in BLACKLIST_PROVINCIAS)
    mentions_local = (
        any(loc.lower() in text_to_search for loc in LOCALIDADES) or
        any(dept.lower() in text_to_search for dept in DEPARTAMENTOS)
    )
    if any(re.search(pat, title_desc_combined, re.IGNORECASE) for pat in BLACKLIST_EVENT_LOCATION_PATTERNS):
        return None
    if mentions_other_province and not mentions_local:
        return None

    # 3. Categorización por reglas
    detected_category = None
    
    # VIENTO / ZONDA
    if any(has_keyword_match(title_desc_combined, word) for word in CONTEXT_WIND):
        detected_category = "otro-climatico"
        for slug, keywords in WIND_MAPPING.items():
            if any(has_keyword_match(text_to_search, kw) for kw in keywords):
                detected_category = slug
                break
                
    # INCENDIOS
    if not detected_category and any(has_keyword_match(title_desc_combined, word) for word in CONTEXT_FIRE):
        is_firearm = any(x in text_to_search for x in [
            "arma de fuego", "armas de fuego", "disparó", "disparo", "dispararon",
            "balearon", "balear", "herido de bala", "herida de bala", "impactos de bala", 
            "recibio disparos", "recibió disparos", "tiros", "disparos", "balacera", "balazo"
        ])
        is_animal = "llamas" in text_to_search and any(a in text_to_search for a in ["animal", "aves", "guanaco", "fauna", "especie", "ejemplar"])
        if not (is_firearm or is_animal):
            detected_category = "incendio"
            for slug, fire_kws in FIRE_MAPPING.items():
                if any(has_keyword_match(text_to_search, kw) for kw in fire_kws):
                    detected_category = slug
                    break
                    
    # ACCIDENTES
    enable_accident_scraping = get_env_variable("ENABLE_ACCIDENT_SCRAPING", "false").lower() == "true"
    if enable_accident_scraping and not detected_category and any(has_keyword_match(title_desc_combined, word) for word in CONTEXT_ACCIDENT):
        is_armed_violence = any(x in text_to_search for x in [
            "balearon", "balear", "herido de bala", "herida de bala", "impactos de bala", 
            "recibio disparos", "recibió disparos", "tiros", "disparos", "apuñalaron", 
            "apunalar", "apuñaló", "apunalo", "herido de arma blanca", "puñalada", "punialada"
        ])
        has_real_crash = any(x in text_to_search for x in ["chocó contra", "choco contra", "colisionaron", "embistió a", "embistio a"])
        
        if is_armed_violence and not has_real_crash:
            pass
        else:
            vuelco_context = [
                "auto", "automóvil", "automovil", "vehículo", "vehiculo", "coche",
                "camión", "camion", "camioneta", "colectivo", "micro", "ómnibus", "omnibus", "bus",
                "moto", "motocicleta", "motociclista", "ciclomotor", "rodado",
                "ciclista", "bicicleta", "bici", "peatón", "peatona", "transeúnte", "transeunte",
                "utilitario", "furgón", "furgon", "trafic", "ambulancia", "patrullero",
                "ruta", "calle", "avenida", "av.", "autopista", "carretera", "asfalto", "calzada",
                "banquina", "zanja", "cuneta", "bache", "semáforo", "semaforo", "esquina",
                "conductor", "conductores", "pasajero", "pasajeros", "volcadura", "tránsito", "transito", "vial"
            ]
            false_positives = [
                "vuelco inesperado", "vuelco en la causa", "vuelco en la investigacion",
                "vuelco en la investigación", "vuelco en el caso", "giro inesperado",
                "cayó detenido", "cayo detenido", "cayó preso", "cayo preso",
                "cayó la banda", "cayo la banda", "cayó una banda", "cayo una banda",
                "cayó por el robo", "cayo por el robo", "cayó por robo", "cayo por robo",
                "cayó por robar", "cayo por robar", "cayó in fraganti", "cayo in fraganti",
                "cayó con las manos", "cayo con las manos", "cayó tras", "cayo tras",
                "cayó acusado", "cayo acusado", "caída de granizo", "caida de granizo",
                "caída del cabello", "caida del cabello", "caída de las ventas", "caida de las ventas",
                "caída del consumo", "caida del consumo"
            ]
            for slug, keywords in ACCIDENT_MAPPING.items():
                if any(has_keyword_match(text_to_search, kw) for kw in keywords):
                    if slug == "vuelco":
                        if any(fp in text_to_search for fp in false_positives):
                            continue
                        if body_text and not any(ctx in text_to_search for ctx in vuelco_context):
                            continue
                    detected_category = slug
                    break
                    
    return detected_category


def analyze_news(title, description, link, fuente_nombre="Noticias San Juan", rule=None, pub_date_str=None, body_text="", conn=None):
    title = clean_html(title)
    description = clean_html(description)

    # ─── CONTROL DE FECHA: Omitir si la publicación es mayor a 3 días ──────────
    from email.utils import parsedate_to_datetime
    pub_date = datetime.now()
    if pub_date_str:
        try:
            # Si ya es una fecha formateada de la DB
            if isinstance(pub_date_str, str) and "-" in pub_date_str and ":" in pub_date_str:
                pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d %H:%M:%S")
            else:
                pub_date = parsedate_to_datetime(pub_date_str)
                pub_date = pub_date.replace(tzinfo=None)
        except Exception as e:
            print(f"[WARNING] No se pudo parsear pubDate '{pub_date_str}': {e}")
            pass

    age_days = (datetime.now() - pub_date).days
    if age_days > 3:
        print(f"[DATE][DISCARD] Noticia omitida por antigüedad ({pub_date.strftime('%Y-%m-%d')}, hace {age_days} días): '{title[:60]}...'")
        return None

    # ─── GUARDIA ANTI-DUPLICADO: Hash de contenido ────────────────────────────
    content_hash = make_content_hash(title, pub_date_str)
    if is_content_processed(content_hash, conn=conn):
        print(f"[HASH-DUP] Noticia ya procesada (mismo título/fecha, distinta URL): '{title[:80]}...'")
        return None

    # ─── FASE 1: Clasificación de categoría y filtros de Python locales ─────────
    # Si las reglas de Python no clasifican esta noticia como un incidente válido,
    # se descarta de inmediato ahorrando llamadas a la API de Gemini.
    detected_category = classify_article_with_python_rules(title, description, body_text, rule)
    if not detected_category:
        print(f"[RULES][DISCARD] No clasifica como incidente o es falso positivo (Python): '{title[:60]}...'")
        return None

    # ─── FASE 4: Geocodificación con texto completo (Gemini + Google Maps) ──────
    gemini_res = None
    gemini_key = get_env_variable("GEMINI_API_KEY")
    if gemini_key:
        gemini_res = extract_location_with_gemini(title, description, body_text)
        if not gemini_res:
            raise GeminiTransientError("No se pudo obtener respuesta válida de Gemini API (posible error, límite o timeout)")

    # Omitir retrospectivas o noticias históricas
    if gemini_res.get("is_retrospective_or_historical"):
        print(f"[GEMINI][DISCARD] Noticia descartada por ser retrospectiva o histórica: '{title[:60]}...'")
        return None

    lat, lon, is_approx, source, loc_type = None, None, True, 'fallback', 'APPROXIMATE'
    resolved = False

    if gemini_res.get("location_query"):
        q_str = gemini_res["location_query"]
        q_is_approx = gemini_res.get("is_approximate", True)
        
        # Ignorar ubicaciones explícitamente desconocidas o genéricas
        q_str_clean = q_str.strip().lower()
        unknown_terms = (
            "desconocido", "desconocida", "desconocido", "desconocida", 
            "fuera de san juan", "sin direccion", "sin dirección", 
            "unknown", "none", "no especifica", "no especificado", 
            "no se especifica", "no menciona", "no determinado"
        )
        if q_str_clean in unknown_terms or not q_str_clean:
            print(f"[GEO][DISCARD] La ubicación extraída es desconocida o genérica: '{q_str}'. Saltando noticia.")
            return None

        res = resolve_geocode(q_str, q_is_approx, conn=conn)
        if res:
            lat, lon, is_approx, source, loc_type = res
            resolved = True

    if not resolved:
        # Intentar fallback por departamento/localidad en base al texto completo (Bug P8)
        text_to_search = title + " " + (description or "") + " " + (body_text or "")
        fallback_coords = get_db_fallback_coords(text_to_search, conn=conn)
        if fallback_coords:
            lat, lon, matched_name, matched_type = fallback_coords
            is_approx = True
            source = 'db_fallback'
            loc_type = 'APPROXIMATE'
            print(f"[GEO][FALLBACK] No se geocodificó por Google, pero se resolvió al centro del {matched_type} '{matched_name}': {lat}, {lon}")
            resolved = True

    if not resolved:
        # Si tampoco se pudo resolver por fallback, descartamos la noticia
        print(f"[GEO][DISCARD] No se pudo geolocalizar de ninguna forma la noticia. Saltando.")
        return None

    # Si Gemini detecta una subcategoría específica válida, refinamos el resultado de Python
    valid_cats = [
        "arboles-caidos", "techo-volado", "corte-energia",
        "incendio-pastizales", "incendio-forestal", "incendio-vivienda", "incendio-vehiculo",
        "granizo", "tormenta-electrica", "inundacion-urbana",
        "creciente-rio", "creciente-quebrada", "corte-ruta-por-agua",
        "derrumbe-ruta", "desprendimiento-rocas", "alud",
        "nevada", "helada", "ola-de-calor", "accidente-climatico",
        "otro-climatico", "desconocido",
        "choque", "vuelco", "atropello", "accidente"
    ]
    if gemini_res and gemini_res.get("category") and gemini_res["category"] not in ("desconocido", "desconocida", None):
        if gemini_res["category"] in valid_cats:
            detected_category = gemini_res["category"]

    is_fatal = gemini_res.get("is_fatal", False) if gemini_res else False
    wind_cause = gemini_res.get("wind_cause", False) if gemini_res else False
    phenomenon_type = gemini_res.get("phenomenon_type", "ninguno") if gemini_res else "ninguno"
    raw_hectares = gemini_res.get("hectares_burned", -1) if gemini_res else -1
    hectares_burned = None if raw_hectares == -1 else raw_hectares
    
    event_date = pub_date
    text_to_search = (title + " " + (description or "") + " " + (body_text or "")).lower()
    if "ayer" in text_to_search or "anoche" in text_to_search:
        from datetime import timedelta
        event_date = pub_date - timedelta(days=1)
        
    # Persistir el hash ANTES de retornar para que futuras corridas no re-geocodifiquen esta noticia
    save_content_hash(content_hash, link or '', conn=conn)

    # Generar una descripción concisa para la UI (máximo ~500 caracteres)
    if description and len(description.strip()) >= 120:
        # Si la descripción de la fuente ya es sustancial, la usamos directamente
        full_description = description.strip()
    elif body_text:
        # Si no hay descripción o es muy corta, usamos los primeros párrafos del cuerpo
        paragraphs = [p.strip() for p in body_text.split("\n") if p.strip()]
        if paragraphs:
            # Tomar hasta los primeros 2 párrafos
            selected_text = " ".join(paragraphs[:2])
            if len(selected_text) > 500:
                selected_text = selected_text[:500].rsplit(' ', 1)[0] + "..."
            full_description = selected_text
        else:
            full_description = description.strip() if description else "Sin descripción."
    else:
        full_description = description.strip() if description else "Sin descripción."

    return {
        "etiqueta": detected_category,
        "titulo": title[:250],
        "descripcion": full_description,
        "latitud": lat,
        "longitud": lon,
        "is_approximate": is_approx,
        "source": source,
        "location_type": loc_type,
        "is_fatal": is_fatal,
        "wind_cause": wind_cause,
        "phenomenon_type": phenomenon_type,
        "hectares_burned": hectares_burned,
        "fuente_nombre": fuente_nombre,
        "fuente_url": link,
        "event_date": event_date.strftime("%Y-%m-%d %H:%M:%S"),
        "source_publish_date": pub_date.strftime("%Y-%m-%d %H:%M:%S"),
        "verificado": False,
        "victim_names": ", ".join(gemini_res.get("victim_names", [])) if (gemini_res and gemini_res.get("victim_names")) else None,
        "has_car": gemini_res.get("has_car", False) if gemini_res else False,
        "has_pickup": gemini_res.get("has_pickup", False) if gemini_res else False,
        "has_utility": gemini_res.get("has_utility", False) if gemini_res else False,
        "has_motorcycle": gemini_res.get("has_motorcycle", False) if gemini_res else False,
        "has_truck": gemini_res.get("has_truck", False) if gemini_res else False,
        "has_bus": gemini_res.get("has_bus", False) if gemini_res else False,
        "has_pedestrian": gemini_res.get("has_pedestrian", False) if gemini_res else False,
        "has_bicycle": gemini_res.get("has_bicycle", False) if gemini_res else False
    }


def send_to_api(incident_data):
    try:
        res = requests.post(API_URL, json=incident_data, headers={'Accept': 'application/json'})
        if res.status_code == 201:
            print(f"[OK] Incidente guardado: {incident_data['fuente_nombre']} - {incident_data['titulo']}")
            return True
        elif res.status_code == 200:
            print(f"[DUPLICADO] {incident_data['titulo']}")
            return True
        else:
            print(f"[ERROR] {res.status_code}: {res.text}")
            return False
    except Exception as e:
        print(f"[CONEXION FALLIDA] No se pudo enviar a la API: {e}")
        return False

def process_queued_articles():
    """Procesa todas las noticias de raw_articles con estado 'queued' utilizando analyze_news"""
    print(f"[{datetime.now()}] Iniciando procesamiento de noticias en cola (raw_articles)...")
    
    # ─── PURGA AUTOMÁTICA DE ARTÍCULOS VIEJOS TERMINALES (Bug P15) ──────────────
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM raw_articles 
            WHERE status IN ('processed', 'ignored')
              AND updated_at < datetime('now', '-7 days')
        """)
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        if deleted > 0:
            print(f"[PROCESADOR][PURGE] {deleted} artículos antiguos purgados de raw_articles.")
    except Exception as e:
        print(f"[PROCESADOR][PURGE][ERROR] No se pudo purgar la base de datos: {e}")

    # ─── OBTENER ARTÍCULOS PARA PROCESAR (Queued y Failed transitorios) (Bug P2) ──
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, description, body, source_name, source_url, publish_date, status, error_message 
            FROM raw_articles 
            WHERE status = 'queued'
               OR (status = 'failed' AND updated_at < datetime('now', '-10 minutes'))
        """)
        queued = cursor.fetchall()
        # Mantenemos conn abierto para el resto del procesamiento (Bug P3)
    except Exception as e:
        print(f"[PROCESADOR][ERROR] No se pudo leer noticias de la DB: {e}")
        try:
            conn.close()
        except Exception:
            pass
        return

    if not queued:
        print("[PROCESADOR] No hay noticias en cola para procesar.")
        conn.close()
        return

    print(f"[PROCESADOR] Se encontraron {len(queued)} noticias pendientes para procesar.")
    SCRAPER_RULES = load_rules()

    global gemini_calls_in_run, google_maps_calls_in_run
    gemini_calls_in_run = 0
    google_maps_calls_in_run = 0

    for row in queued:
        art_id, title, description, body_text, source_name, source_url, publish_date, status, current_error = row
        print(f"[PROCESADOR][ARTICULO] Procesando ID {art_id} (Estado: {status}): '{title[:50]}...'")

        # Intentar obtener la configuración para este dominio
        from urllib.parse import urlparse
        parsed_url = urlparse(source_url)
        domain = parsed_url.netloc.replace("www.", "")
        rule = get_source_rule(SCRAPER_RULES, domain)

        try:
            # Procesar el artículo usando la lógica unificada de analyze_news (Bug P3: pasar conn)
            incident = analyze_news(
                title=title,
                description=description,
                link=source_url,
                fuente_nombre=source_name,
                rule=rule,
                pub_date_str=publish_date,
                body_text=body_text,
                conn=conn
            )

            # Re-obtener cursor de la conexión compartida
            cursor = conn.cursor()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if incident:
                # Si está activado el enriquecimiento climático (Fase 2)
                enable_climate = get_env_variable("ENABLE_CLIMATE_ENRICHMENT", "true").lower() == "true"
                if enable_climate:
                    try:
                        from climate_enricher import enrich_incident_data
                        print(f"[CLIMATE] Enriqueciendo datos climáticos para: '{incident['titulo'][:50]}...'")
                        c_data = enrich_incident_data(incident["latitud"], incident["longitud"], incident["event_date"])
                        incident.update(c_data)
                        incident["climate_enriched"] = True
                    except Exception as ce:
                        print(f"[CLIMATE][ERROR] Falló enriquecimiento climático en caliente: {ce}")

                # Liberar bloqueos de SQLite antes del request de red a la API (evita 504 por lock contention)
                conn.commit()

                # Si clasifica como incidente y se geocodifica, enviar a Laravel API
                api_success = send_to_api(incident)

                cursor = conn.cursor()
                if api_success:
                    # Actualizar estado a 'processed'
                    cursor.execute(
                        "UPDATE raw_articles SET status = 'processed', error_message = NULL, updated_at = ? WHERE id = ?",
                        (now_str, art_id)
                    )
                else:
                    raise Exception("Fallo en la comunicación con la API (ver log de send_to_api)")
            else:
                # Si no clasifica como incidente, marcar como 'ignored'
                conn.commit()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE raw_articles SET status = 'ignored', error_message = NULL, updated_at = ? WHERE id = ?",
                    (now_str, art_id)
                )

            conn.commit()

        except Exception as e:
            error_msg = str(e)
            print(f"[PROCESADOR][ERROR] Error procesando artículo ID {art_id}: {error_msg}")
            
            # Contar reintentos en el error_message (Bug P1 & P2)
            try:
                attempts = 1
                if status == 'failed' and current_error:
                    # Buscar el patrón [Intento X/3]
                    m = re.match(r"^\[Intento (\d+)/3\]", current_error)
                    if m:
                        attempts = int(m.group(1)) + 1
                
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Si superamos el límite de 3 intentos, lo marcamos como 'failed_permanently'
                if attempts > 3:
                    final_status = 'failed_permanently'
                    final_msg = f"[Límite reintentos] {error_msg}"
                    print(f"[PROCESADOR][ARTICULO] ID {art_id} superó el límite de 3 reintentos. Marcado como 'failed_permanently'.")
                else:
                    final_status = 'failed'
                    final_msg = f"[Intento {attempts}/3] {error_msg}"
                
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE raw_articles SET status = ?, error_message = ?, updated_at = ? WHERE id = ?",
                    (final_status, final_msg, now_str, art_id)
                )
                conn.commit()
            except Exception as e2:
                print(f"[PROCESADOR][ERROR] No se pudo guardar el estado de error en la DB para ID {art_id}: {e2}")

        # Pequeña pausa para no saturar APIs si es procesado
        time.sleep(3)

    # Cerrar la conexión compartida
    try:
        conn.close()
    except Exception:
        pass
    print(f"[{datetime.now()}] Procesamiento finalizado.")

def scrape_html():
    print(f"[{datetime.now()}] Iniciando barrido HTML...")
    session = requests.Session()
    SCRAPER_RULES = load_rules()
    conn = sqlite3.connect(DB_PATH)
    try:
        for domain, source_config in SCRAPER_RULES["sources"].items():
            rule = get_source_rule(SCRAPER_RULES, domain)
            if rule["type"] != "html":
                continue
            
            has_error = False
            last_error = None
            
            scrape_urls = rule.get("scrape_urls", [])
            for scrape_url in scrape_urls:
                try:
                    medio = MEDIA_NAMES.get(domain, domain)
                    print(f"Scrapeando HTML: {medio} ({scrape_url})")
                    response = session.get(scrape_url, headers=get_headers(scrape_url), timeout=15, verify=False)
                    if response.status_code == 200:
                        html_text = response.text
                        matches = re.finditer(rule['article_selector'], html_text, re.DOTALL)
                        for match in matches:
                            link = match.group(1)
                            title = html.unescape(re.sub(r'<[^>]+>', '', match.group(2)).strip())
                            desc = match.group(3).strip() if len(match.groups()) > 2 else ""
                            desc = html.unescape(re.sub(r'<[^>]+>', '', desc))
                            if not link.startswith('http'):
                                from urllib.parse import urlparse
                                parsed_uri = urlparse(scrape_url)
                                base_domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
                                link = base_domain + link
                            if rule["duplicate_check"] and link:
                                inc_exists, inc_is_approx, old_body = check_incident_precision(link, conn=conn)
                                if inc_exists:
                                    if inc_is_approx:
                                        new_body = fetch_article_text(link)
                                        if new_body and old_body:
                                            if (len(new_body) - len(old_body)) >= 15:
                                                print(f"[RE-EVAL][DISPARADOR] Noticia ampliada detectada para {link} (Cuerpo creció de {len(old_body)} a {len(new_body)} chars). Re-encolando...")
                                                cursor = conn.cursor()
                                                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                cursor.execute("""
                                                    UPDATE raw_articles 
                                                    SET body = ?, status = 'queued', error_message = NULL, updated_at = ? 
                                                    WHERE source_url = ?
                                                """, (new_body, now_str, link))
                                                conn.commit()
                                                continue
                                    print(f"[DB DUPLICADO] Saltando URL ya procesada: {link}")
                                    continue
                            
                            potential_category = classify_article_with_python_rules(title, desc, None, rule)
                            body_text = ""
                            
                            if potential_category:
                                deep_fetch_enabled = rule.get("deep_fetch", True)
                                if deep_fetch_enabled and link and link.startswith("http"):
                                    body_text = fetch_article_text(link)
                                save_raw_article(title, desc, body_text, link, medio, status='queued', conn=conn)
                            else:
                                print(f"[RULES][INGEST-SKIP] Titular no corresponde a incidente (ignorado): '{title[:60]}...'")
                    else:
                        has_error = True
                        last_error = f"HTTP Error status code {response.status_code} for URL {scrape_url}"
                except Exception as e:
                    has_error = True
                    last_error = str(e)
                    print(f"Error procesando HTML de {domain} - {scrape_url}: {e}")
            
            # Update scraper_sources table for this domain
            try:
                cursor = conn.cursor()
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if has_error:
                    cursor.execute("""
                        UPDATE scraper_sources 
                        SET last_scraped_at = ?, is_broken = 1, error_message = ? 
                        WHERE domain = ?
                    """, (now_str, last_error, domain))
                else:
                    cursor.execute("""
                        UPDATE scraper_sources 
                        SET last_scraped_at = ?, is_broken = 0, error_message = NULL 
                        WHERE domain = ?
                    """, (now_str, domain))
                conn.commit()
            except Exception as db_err:
                print(f"[MONITOR][ERROR] No se pudo guardar estado de monitoreo para {domain}: {db_err}")
        conn.commit()
    finally:
        try:
            conn.close()
        except Exception:
            pass

def scrape_rss():
    print(f"[{datetime.now()}] Iniciando barrido de RSS...")
    SCRAPER_RULES = load_rules()
    conn = sqlite3.connect(DB_PATH)
    try:
        for domain, source_config in SCRAPER_RULES["sources"].items():
            rule = get_source_rule(SCRAPER_RULES, domain)
            if rule["type"] != "rss":
                continue
            
            has_error = False
            last_error = None
            
            scrape_urls = rule.get("scrape_urls", [])
            for feed_url in scrape_urls:
                try:
                    fuente_nombre = MEDIA_NAMES.get(domain, "Noticias San Juan")
                    print(f"Leyendo: {fuente_nombre} ({feed_url})")
                    response = requests.get(feed_url, headers=get_headers(feed_url), timeout=15, verify=False)
                    if response.status_code == 200:
                        root = ET.fromstring(response.content)
                        for item in root.findall('.//item'):
                            title_tag = item.find('title')
                            desc_tag = item.find('description')
                            title = html.unescape(title_tag.text if title_tag is not None and title_tag.text else '')
                            desc = html.unescape(desc_tag.text if desc_tag is not None and desc_tag.text else '')
                            link = item.find('link').text if item.find('link') is not None else ''
                            pub_date_tag = item.find('pubDate')
                            pub_date_str = pub_date_tag.text if pub_date_tag is not None else None
                            
                            if rule["duplicate_check"] and link:
                                inc_exists, inc_is_approx, old_body = check_incident_precision(link, conn=conn)
                                if inc_exists:
                                    if inc_is_approx:
                                        new_body = fetch_article_text(link)
                                        if new_body and old_body:
                                            if (len(new_body) - len(old_body)) >= 15:
                                                print(f"[RE-EVAL][DISPARADOR] Noticia ampliada detectada para {link} (Cuerpo creció de {len(old_body)} a {len(new_body)} chars). Re-encolando...")
                                                cursor = conn.cursor()
                                                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                cursor.execute("""
                                                    UPDATE raw_articles 
                                                    SET body = ?, status = 'queued', error_message = NULL, updated_at = ? 
                                                    WHERE source_url = ?
                                                """, (new_body, now_str, link))
                                                conn.commit()
                                                continue
                                    print(f"[DB DUPLICADO] Saltando URL ya procesada: {link}")
                                    continue
                            if title:
                                potential_category = classify_article_with_python_rules(title, desc, None, rule)
                                body_text = ""
                                
                                if potential_category:
                                    deep_fetch_enabled = rule.get("deep_fetch", True)
                                    if deep_fetch_enabled and link and link.startswith("http"):
                                        body_text = fetch_article_text(link)
                                    save_raw_article(title, desc, body_text, link, fuente_nombre, pub_date_str, status='queued', conn=conn)
                                else:
                                    print(f"[RULES][INGEST-SKIP] Titular no corresponde a incidente (ignorado): '{title[:60]}...'")
                    else:
                        has_error = True
                        last_error = f"HTTP Error status code {response.status_code} for URL {feed_url}"
                except Exception as e:
                    has_error = True
                    last_error = str(e)
                    print(f"Error procesando el feed {feed_url}: {e}")
            
            # Update scraper_sources table for this domain
            try:
                cursor = conn.cursor()
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if has_error:
                    cursor.execute("""
                        UPDATE scraper_sources 
                        SET last_scraped_at = ?, is_broken = 1, error_message = ? 
                        WHERE domain = ?
                    """, (now_str, last_error, domain))
                else:
                    cursor.execute("""
                        UPDATE scraper_sources 
                        SET last_scraped_at = ?, is_broken = 0, error_message = NULL 
                        WHERE domain = ?
                    """, (now_str, domain))
                conn.commit()
            except Exception as db_err:
                print(f"[MONITOR][ERROR] No se pudo guardar estado de monitoreo para {domain}: {db_err}")
        conn.commit()
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--daemon', action='store_true', help='Ejecutar en modo bucle infinito cada 1 hora')
    args = parser.parse_args()
    if args.daemon:
        while True:
            scrape_rss()
            scrape_html()
            process_queued_articles()
            print(f"[{datetime.now()}] Esperando 30 minutos para el próximo barrido...")
            time.sleep(1800)
    else:
        scrape_rss()
        scrape_html()
        process_queued_articles()
