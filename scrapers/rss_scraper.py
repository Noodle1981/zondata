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

# Configuración Global - Usamos Googlebot para maximizar compatibilidad y evitar bloqueos 403
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9',
    'Connection': 'keep-alive'
}

API_URL = get_env_variable("APP_URL", "http://127.0.0.1:8000") + "/api/incidents"

from load_rules import load_rules, get_source_rule
RULES = load_rules()
# ─── Palabras de pre-filtro de TÍTULO ───────────────────────────────────────
# Estas listas son el PRIMER filtro: si el título no contiene ninguna de estas
# palabras, el artículo se descarta sin hacer deep fetch ni geocoding.
# Deben ser ESPECÍFICAS al hecho (no genéricas como "tránsito" o "vial").

# Viento / Zonda: palabras que indican daño concreto por viento
CONTEXT_WIND = [
    # Fenómenos
    "zonda", "viento zonda", "viento sur", "ráfagas", "vientos fuertes",
    "tormenta de viento", "temporal de viento",
    # Daños concretos (también aplica sin contexto de viento explícito)
    "voló el techo", "volaron techos", "voló un techo", "techo volado",
    "árbol caído", "arboles caidos", "árboles caídos", "árbol cayó",
    "cables caídos", "cables cortados", "sin luz por viento",
    "voladura de techo", "voladuras de techo",
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
    "arboles": ["árbol", "arbol", "ramas", "caída de árboles", "caida de arbol"],
    "corte": ["corte de luz", "sin luz", "energía san juan", "transformador", "cables cortados"],
    "incendio": ["incendio", "fuego", "bomberos", "pastizales"],
    "techo": ["techo", "voladura", "chapa"]
}

ACCIDENT_MAPPING = {
    "choque": ["choque", "chocó", "choco", "chocar", "chocar", "chocaron", "colisión", "colision", "impacto", "impactó", "siniestro vial", "accidente", "vial"],
    "vuelco": ["vuelco", "volcó", "despistó", "cayó", "caída", "caida"],
    "atropello": ["atropelló", "embistió", "peatón", "arrolló", "moto", "motociclista"]
}

FIRE_MAPPING = {
    "incendio-vivienda": ["casa", "vivienda", "departamento", "edificio", "habitación"],
    "incendio-pastizales": ["pastizales", "campo", "lote", "baldío", "maleza"],
    "incendio-vehiculo": ["auto", "camioneta", "camión", "vehículo", "moto", "trafic", "furgón", "furgon", "colectivo"]
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

def get_cached_coords(query):
    """
    Consulta si la query ya fue geolocalizada previamente.
    Retorna (latitude, longitude, is_approximate, source, location_type) o None.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT latitude, longitude, is_approximate, source, location_type "
            "FROM geocoding_cache WHERE query = ?",
            (query,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0], row[1], bool(row[2]), row[3], row[4]
    except Exception as e:
        print(f"[ERROR] Error al consultar caché: {e}")
    return None

def save_to_cache(query, lat, lon, is_approx, source='nominatim', location_type='GEOMETRIC_CENTER'):
    """
    Guarda una geolocalización en la caché para evitar futuras consultas de API.
    - source: 'nominatim' | 'google' | 'fallback'
    - location_type: valor de Google ('ROOFTOP', 'RANGE_INTERPOLATED', 'GEOMETRIC_CENTER', 'APPROXIMATE')
                     o 'GEOMETRIC_CENTER' por defecto para resultados de Nominatim.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO geocoding_cache
                (query, latitude, longitude, is_approximate, source, location_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (query, lat, lon, int(is_approx), source, location_type))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ERROR] Error al guardar en caché: {e}")

# Inicializar caché en el arranque (crea tabla y aplica migraciones)
init_cache_db()

def is_url_processed(url):
    """Verifica en la BD local si la URL ya fue ingresada para evitar raspado redundante"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM incidents WHERE source_url = ?", (url,))
        row = cursor.fetchone()
        conn.close()
        return row is not None
    except Exception as e:
        print(f"[ERROR] Error al verificar URL duplicada en la DB: {e}")
        return False

def make_content_hash(title: str, pub_date_str: str | None) -> str:
    """
    Genera un hash MD5 del título normalizado + fecha de publicación.
    Detecta la misma noticia publicada con distinta URL (muy común en diarios sanjuaninos).
    """
    normalized = normalize_text(title.strip().lower())
    raw = f"{normalized}|{pub_date_str or ''}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()

def is_content_processed(content_hash: str) -> bool:
    """Retorna True si ya procesamos una noticia con este hash de contenido."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM content_hash_cache WHERE hash = ?", (content_hash,))
        row = cursor.fetchone()
        conn.close()
        return row is not None
    except Exception as e:
        print(f"[ERROR] Error al verificar hash de contenido: {e}")
        return False

def save_content_hash(content_hash: str, source_url: str):
    """Persiste el hash de contenido para que futuras corridas no re-geocodifiquen la misma noticia."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO content_hash_cache (hash, source_url) VALUES (?, ?)",
            (content_hash, source_url)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ERROR] Error al guardar hash de contenido: {e}")

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
    "alerta", "pronóstico", "pronostico", "precaución", "precaucion", "recomiendan", 
    "prevención", "prevencion", "llegaría", "llegaria", "internacional", "mundo",
    "escuela", "curso", "capacitación", "capacitacion", "proyecto", "campaña", 
    "historia de", "entrevista", "emicar", "clases", "inscripción", "inscripcion",
    "allanamiento", "detenido", "detenidos", "droga", "estupefacientes", "animales silvestres",
    "fauna", "caza ilegal", "secuestraron armas",
    "obra vial", "obras viales", "obra pública", "obra publica", "obras públicas", "obras publicas",
    "licitación", "licitacion", "licitar", "remodelación", "remodelacion",
    "apertura de sobres", "pavimentación", "pavimentacion", "bacheo", "repavimentación", "repavimentacion",
    "seguridad vial", "educación vial", "educacion vial", "taller de", "charlas de"
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

def resolve_geocode(query_str, is_approx):
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
    cached = get_cached_coords(query_str)
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
            source='google', location_type=g_loc_type
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
        response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
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


def analyze_news(title, description, link, fuente_nombre="Noticias San Juan", rule=None, pub_date_str=None):
    title = clean_html(title)
    description = clean_html(description)

    # ─── GUARDIA ANTI-DUPLICADO: Hash de contenido ────────────────────────────
    # Genera un hash MD5 del título normalizado + fecha de publicación.
    # Si ya procesamos una noticia con este contenido (aunque tenga distinta URL),
    # la descartamos ANTES de hacer cualquier deep fetch o llamada de geocoding.
    content_hash = make_content_hash(title, pub_date_str)
    if is_content_processed(content_hash):
        print(f"[HASH-DUP] Noticia ya procesada (mismo título/fecha, distinta URL): '{title[:80]}...'")
        return None

    text_to_search = (title + " " + description).lower()
    # Evitar falsos positivos de "fuego" en palabras que no refieren a un incendio (ej. matafuegos)
    text_to_search = text_to_search.replace("matafuegos", "").replace("matafuego", "")
    if any(black_word in text_to_search for black_word in BLACKLIST_KEYWORDS):
        return None
    if rule and rule.get("ignore_terms"):
        if any(term in text_to_search for term in rule["ignore_terms"]):
            return None

    # ─── FASE 1: Pre-filtro por título/descripción ────────────────────────────
    # Si el título/descripción no contiene ninguna señal relevante (accidente,
    # incendio, viento), se descarta SIN hacer deep fetch para no desperdiciar
    # ancho de banda ni provocar 429 de Nominatim con texto de menús/secciones.
    ALL_CONTEXT_KEYWORDS = CONTEXT_WIND + CONTEXT_FIRE + CONTEXT_ACCIDENT
    if not any(has_keyword_match(text_to_search, kw) for kw in ALL_CONTEXT_KEYWORDS):
        return None

    # ─── FASE 2: Filtros de ubicación ─────────────────────────────────────────
    mentions_other_province = any(prov in text_to_search for prov in BLACKLIST_PROVINCIAS)
    mentions_local = (
        any(loc.lower() in text_to_search for loc in LOCALIDADES) or
        any(dept.lower() in text_to_search for dept in DEPARTAMENTOS)
    )
    title_desc_combined = (title + " " + description).lower()
    if any(re.search(pat, title_desc_combined, re.IGNORECASE) for pat in BLACKLIST_EVENT_LOCATION_PATTERNS):
        return None
    if mentions_other_province and not mentions_local:
        return None

    # ─── FASE 3: Deep fetch (solo si el título tenía señal relevante) ──────────
    # Leer el cuerpo completo para obtener más contexto geográfico y de categoría.
    deep_fetch_enabled = rule.get("deep_fetch", True) if rule else True
    body_text = ""
    if deep_fetch_enabled and link and link.startswith("http"):
        body_text = fetch_article_text(link)
        if body_text:
            text_to_search += " " + body_text.lower()

    # ─── FASE 4: Geocodificación con texto completo ────────────────────────────
    res = geocoding_funnel(title, rule)
    if res and not res[2]:
        lat, lon, is_approx, source, loc_type = res
    else:
        full_res = geocoding_funnel(title + " " + description, rule)
        if full_res:
            lat, lon, is_approx, source, loc_type = full_res
        else:
            lat, lon, is_approx, source, loc_type = None, None, True, 'fallback', 'APPROXIMATE'

    # Intentar mejorar coordenadas con el cuerpo si aún son aproximadas
    if body_text and (is_approx or lat is None):
        deep_res = geocoding_funnel(body_text, rule)
        if deep_res:
            d_lat, d_lon, d_is_approx, d_source, d_loc_type = deep_res
            if not d_is_approx or lat is None:
                lat, lon, is_approx, source, loc_type = d_lat, d_lon, d_is_approx, d_source, d_loc_type

    # ─── FASE 5: Detección de categoría ────────────────────────────────────────
    # Usamos title_desc_combined para verificar el CONTEXTO principal (evita falsos
    # positivos si el cuerpo menciona "impactó" en una nota de un puma, por ej).
    # Usamos text_to_search (que incluye el cuerpo) para buscar detalles en el MAPPING.
    detected_category = None
    
    if any(has_keyword_match(title_desc_combined, word) for word in CONTEXT_WIND):
        for slug, keywords in WIND_MAPPING.items():
            if any(has_keyword_match(text_to_search, kw) for kw in keywords):
                detected_category = slug
                break
                
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
                    
    if not detected_category and any(has_keyword_match(title_desc_combined, word) for word in CONTEXT_ACCIDENT):
        # Guardia contra falsos positivos: incidentes de violencia armada, disparos o asaltos
        # que no son siniestros viales sino delitos policiales o crímenes de sangre.
        is_armed_violence = any(x in text_to_search for x in [
            "balearon", "balear", "herido de bala", "herida de bala", "impactos de bala", 
            "recibio disparos", "recibió disparos", "tiros", "disparos", "apuñalaron", 
            "apunalar", "apuñaló", "apunalo", "herido de arma blanca", "puñalada", "punialada"
        ])
        has_real_crash = any(x in text_to_search for x in ["chocó contra", "choco contra", "colisionaron", "embistió a", "embistio a"])
        
        if is_armed_violence and not has_real_crash:
            # Es un hecho policial de sangre, no un accidente vial. Se saltea.
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
                    if not any(ctx in text_to_search for ctx in vuelco_context):
                        continue
                detected_category = slug
                break

    if not detected_category or lat is None:
        return None

    is_fatal = any(has_keyword_match(text_to_search, kw) for kw in FATAL_KEYWORDS)
    
    from email.utils import parsedate_to_datetime
    
    pub_date = datetime.now()
    if pub_date_str:
        try:
            # RSS pubDate typically uses RFC 2822
            pub_date = parsedate_to_datetime(pub_date_str)
            # Remove timezone info to match our DB format (naive local)
            pub_date = pub_date.replace(tzinfo=None)
        except Exception as e:
            print(f"[WARNING] No se pudo parsear pubDate '{pub_date_str}': {e}")
            pass
            
    event_date = pub_date
    if "ayer" in text_to_search or "anoche" in text_to_search:
        from datetime import timedelta
        event_date = pub_date - timedelta(days=1)
        
    # Persistir el hash ANTES de retornar para que futuras corridas no re-geocodifiquen esta noticia
    save_content_hash(content_hash, link or '')

    # Concatenar la descripción corta y el cuerpo completo para que la API de Laravel 
    # tenga todo el texto disponible para la extracción de nombres de víctimas y análisis.
    full_description = description if description else ""
    if body_text:
        # Evitar duplicar el copete si ya está al inicio del cuerpo
        cleaned_body = body_text.strip()
        if full_description and cleaned_body.startswith(full_description[:100]):
            full_description = cleaned_body
        else:
            full_description = (full_description + "\n\n" + cleaned_body).strip()
            
    if not full_description:
        full_description = "Sin descripción."

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
        "fuente_nombre": fuente_nombre,
        "fuente_url": link,
        "event_date": event_date.strftime("%Y-%m-%d %H:%M:%S"),
        "source_publish_date": pub_date.strftime("%Y-%m-%d %H:%M:%S"),
        "verificado": False
    }


def send_to_api(incident_data):
    try:
        res = requests.post(API_URL, json=incident_data, headers={'Accept': 'application/json'})
        if res.status_code == 201:
            print(f"[OK] Incidente guardado: {incident_data['fuente_nombre']} - {incident_data['titulo']}")
        elif res.status_code == 200:
            print(f"[DUPLICADO] {incident_data['titulo']}")
        else:
            print(f"[ERROR] {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[CONEXION FALLIDA] No se pudo enviar a la API: {e}")

def scrape_html():
    print(f"[{datetime.now()}] Iniciando barrido HTML...")
    session = requests.Session()
    SCRAPER_RULES = load_rules()
    for domain, source_config in SCRAPER_RULES["sources"].items():
        rule = get_source_rule(SCRAPER_RULES, domain)
        if rule["type"] != "html":
            continue
        scrape_urls = rule.get("scrape_urls", [])
        for scrape_url in scrape_urls:
            try:
                medio = MEDIA_NAMES.get(domain, domain)
                print(f"Scrapeando HTML: {medio} ({scrape_url})")
                response = session.get(scrape_url, headers=HEADERS, timeout=15, verify=False)
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
                        if rule["duplicate_check"] and link and is_url_processed(link):
                            print(f"[DB DUPLICADO] Saltando URL ya procesada: {link}")
                            continue
                        incident = analyze_news(title, desc, link, medio, rule)
                        if incident:
                            send_to_api(incident)
            except Exception as e:
                print(f"Error procesando HTML de {domain} - {scrape_url}: {e}")

def scrape_rss():
    print(f"[{datetime.now()}] Iniciando barrido de RSS...")
    SCRAPER_RULES = load_rules()
    for domain, source_config in SCRAPER_RULES["sources"].items():
        rule = get_source_rule(SCRAPER_RULES, domain)
        if rule["type"] != "rss":
            continue
        scrape_urls = rule.get("scrape_urls", [])
        for feed_url in scrape_urls:
            try:
                fuente_nombre = MEDIA_NAMES.get(domain, "Noticias San Juan")
                print(f"Leyendo: {fuente_nombre} ({feed_url})")
                response = requests.get(feed_url, headers=HEADERS, timeout=15, verify=False)
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
                        
                        if rule["duplicate_check"] and link and is_url_processed(link):
                            print(f"[DB DUPLICADO] Saltando URL ya procesada: {link}")
                            continue
                        if title:
                            incident = analyze_news(title, desc, link, fuente_nombre, rule, pub_date_str)
                            if incident:
                                send_to_api(incident)
                                time.sleep(1)
            except Exception as e:
                print(f"Error procesando el feed {feed_url}: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--daemon', action='store_true', help='Ejecutar en modo bucle infinito cada 1 hora')
    args = parser.parse_args()
    if args.daemon:
        while True:
            scrape_rss()
            scrape_html()
            print(f"[{datetime.now()}] Esperando 30 minutos para el próximo barrido...")
            time.sleep(1800)
    else:
        scrape_rss()
        scrape_html()
