import os
import requests
import xml.etree.ElementTree as ET
import time
import sqlite3
import re
import json
from datetime import datetime
import html
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

# URL dinámica desde el .env (por ejemplo http://zondata.test o http://127.0.0.1:8000)
APP_URL = get_env_variable("APP_URL", "http://zondata.test")
API_URL = f"{APP_URL.rstrip('/')}/api/incidents"

RSS_FEEDS = [
    "https://diariodecuyo.com.ar/rss/pages/policiales.xml",
    "https://diariodecuyo.com.ar/rss/pages/san-juan.xml",
    "https://www.tiempodesanjuan.com/rss/pages/Policiales.xml",
    "https://www.tiempodesanjuan.com/rss/pages/home.xml",
    "https://www.diariohuarpe.com/rss/policiales.xml",
    "https://www.diariohuarpe.com/rss/portada.xml",
    "https://www.nuevodiariosanjuan.com.ar/feed",
    "https://www.diariolaprovinciasj.com/rss",
    "https://canal4sanjuan.com.ar/feed/",
    "https://www.canal13sanjuan.com/rss",
    "https://nuevomundosj.com.ar/category/policiales/feed/",
    "https://www.telesoldiario.com/rss"
]

HTML_SOURCES = [
    {
        "url": "https://diariomovil.info/categoria/4/san-juan",
        "medio": "Diario Móvil",
        "article_selector": r'<div[^>]*class="[^"]*post[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>.*?<h[23][^>]*class="[^"]*titulo[^"]*"[^>]*>(.*?)</h[23]>.*?<div[^>]*class="[^"]*resumen[^"]*"[^>]*>(.*?)</div>',
    },
    {
        "url": "https://www.0264noticias.com.ar/policiales",
        "medio": "0264Noticias",
        "article_selector": r'<a[^>]*class="[^"]*w-full[^"]*"[^>]*href="(/noticias/[^"]+)"[^>]*>(?:\s*<h3[^>]*>.*?</h3>)?\s*<h2[^>]*>(.*?)</h2>\s*</a>',
    },
    {
        "url": "https://www.sanjuan8.com/policiales",
        "medio": "San Juan 8",
        "article_selector": r'<h[23][^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>\s*</h[23]>',
    }
]

# Palabras de contexto Viento
CONTEXT_WIND = ["zonda", "viento sur", "ráfagas", "viento", "vientos"]

# Palabras de contexto Accidentes
CONTEXT_ACCIDENT = ["accidente", "siniestro vial", "tránsito", "transito", "choque", "vuelco", "vial", "falleció", "murió", "muerte", "víctima fatal", "deceso"]

# Palabras de contexto Incendios
CONTEXT_FIRE = ["incendio", "llamas", "bomberos", "quemó", "quemo", "siniestro ígneo", "fuego", "incineró", "incinero", "quemar", "quemados", "incinerados"]

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
    "choque": ["choque", "colisión", "impacto", "chocó", "impactó", "siniestro vial", "accidente", "vial"],
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
    """Inicializa la tabla de caché de geolocalización si no existe"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS geocoding_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT UNIQUE,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                is_approximate INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ERROR] No se pudo inicializar la tabla de caché: {e}")

def get_cached_coords(query):
    """Consulta si la query ya fue geolocalizada previamente"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT latitude, longitude, is_approximate FROM geocoding_cache WHERE query = ?", (query,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0], row[1], bool(row[2])
    except Exception as e:
        print(f"[ERROR] Error al consultar caché: {e}")
    return None

def save_to_cache(query, lat, lon, is_approx):
    """Guarda una geolocalización en la caché para evitar futuras consultas de API"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO geocoding_cache (query, latitude, longitude, is_approximate)
            VALUES (?, ?, ?, ?)
        """, (query, lat, lon, int(is_approx)))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ERROR] Error al guardar en caché: {e}")

# Inicializar caché en el arranque
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

def clean_locality_name(name):
    # Quitar parte después de guión (ej: "Vallecito - Paraje..." -> "Vallecito")
    name_clean = name.split('-')[0].strip()
    # Quitar prefijos comunes usando el patrón del JSON
    for pattern in GEO_RULES.get("clean_prefixes", []):
        name_clean = re.sub(pattern, '', name_clean, flags=re.IGNORECASE)
    return name_clean.strip()

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

geolocator = Nominatim(user_agent="zondata_scraper")

def is_within_bounds(lat, lon):
    return BOUNDING_BOX[0] <= lat <= BOUNDING_BOX[1] and BOUNDING_BOX[2] <= lon <= BOUNDING_BOX[3]

def resolve_geocode(query_str, is_approx):
    """
    Resuelve una geolocalización utilizando primero la caché local y, si no existe,
    realiza la consulta externa (Nominatim) y almacena el resultado exitoso en caché.
    """
    # 1. Consultar caché local
    cached = get_cached_coords(query_str)
    if cached is not None:
        return cached[0], cached[1] # lat, lon

    # 2. Si no está en caché, geocodificar con Nominatim
    try:
        location = geolocator.geocode(query_str, timeout=10)
        if location and is_within_bounds(location.latitude, location.longitude):
            # Guardar en la caché local
            save_to_cache(query_str, location.latitude, location.longitude, is_approx)
            return location.latitude, location.longitude
    except Exception as e:
        print(f"[WARNING] Falló consulta externa para '{query_str}': {e}")
        pass
    return None

def sanitize_location_text(text):
    """Limpia el texto de falsos positivos de ubicación como Hospital Rawson"""
    cleaned = text
    cleaned = re.sub(r'hospital(?:\s+dr\.?)?(?:\s+guillermo)?\s+rawson', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'hospital\s+rawson', '', cleaned, flags=re.IGNORECASE)
    return cleaned

def get_hierarchical_context(text):
    """
    Busca contexto siguiendo la prioridad: Localidad -> Departamento -> Provincia
    """
    text = sanitize_location_text(text)
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
            
            return f"{LOCALIDADES_CONTEXT[loc]}, San Juan, Argentina"

    # 2. Prioridad: Departamento
    for dept in DEPARTAMENTOS:
        pattern = r'\b' + re.escape(dept) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            return f"{dept}, San Juan, Argentina"
            
    return "San Juan, Argentina"

def geocoding_funnel(text):
    # Limpiar el texto de ruidos geográficos (Buenos Aires, etc) antes de buscar patrones
    text_sanitized = sanitize_location_text(text)
    text_clean = clean_location_query(text_sanitized)
    local_context = get_hierarchical_context(text_sanitized)
    
    # 1. Caso especial: Ruta y Calle numérica (ej. Ruta 40 y Calle 9 o Calles 9 y 10)
    ruta_match = re.search(r"([Rr]uta\s+\d+)", text_clean, re.IGNORECASE)
    calle_num_match = re.search(r"(?:[Cc]alle[s]?)\s+(\d+)", text_clean, re.IGNORECASE)
    if ruta_match and calle_num_match:
        ruta = ruta_match.group(1)
        calle_num = calle_num_match.group(1)
        query = f"{ruta} & Calle {calle_num}, {local_context}"
        coords = resolve_geocode(query, False)
        if coords:
            return coords[0], coords[1], False

    # 2. Caso especial: Intersección de calle numérica y otra calle numérica (ej. Calle 9 y 10)
    calle_num_interseccion = re.search(r"[Cc]alle[s]?\s+(\d+)\s+(?:y|e|entre)\s+(\d+)", text_clean, re.IGNORECASE)
    if calle_num_interseccion:
        c1 = calle_num_interseccion.group(1)
        c2 = calle_num_interseccion.group(2)
        query = f"Calle {c1} & Calle {c2}, {local_context}"
        coords = resolve_geocode(query, False)
        if coords:
            return coords[0], coords[1], False

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
                return coords[0], coords[1], False
            if local_context != "San Juan, Argentina":
                coords_fallback = resolve_geocode(f"{query}, San Juan, Argentina", False)
                if coords_fallback:
                    return coords_fallback[0], coords_fallback[1], False

    for pattern in linear_precise_patterns:
        match = re.search(pattern, text_clean)
        if match:
            query = " ".join(filter(None, match.groups()))
            coords = resolve_geocode(f"{query}, {local_context}", False)
            if coords:
                return coords[0], coords[1], False
            if local_context != "San Juan, Argentina":
                coords_fallback = resolve_geocode(f"{query}, San Juan, Argentina", False)
                if coords_fallback:
                    return coords_fallback[0], coords_fallback[1], False

    for pattern in approximate_patterns:
        match = re.search(pattern, text_clean)
        if match:
            query = " ".join(filter(None, match.groups()))
            coords = resolve_geocode(f"{query}, {local_context}", True)
            if coords:
                return coords[0], coords[1], True

    for loc in LOCALIDADES:
        if loc.lower() in text.lower():
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
                return coords[0], coords[1], True

    for dept in DEPARTAMENTOS:
        if dept.lower() in text.lower():
            coords = resolve_geocode(f"{dept}, San Juan, Argentina", True)
            if coords:
                return coords[0], coords[1], True

    if any(loc.lower() in text.lower() for loc in LOCALIDADES) or any(dept.lower() in text.lower() for dept in DEPARTAMENTOS) or "san juan" in text.lower():
        return -31.5375, -68.53639, True
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

def fetch_article_text(url):
    """Descarga el cuerpo de la noticia y extrae el texto de las etiquetas de párrafo"""
    try:
        print(f"[DEEP FETCH] Buscando detalles en la URL: {url}")
        response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        if response.status_code == 200:
            html_content = response.text
            p_matches = re.findall(r'<p[^>]*>(.*?)</p>', html_content, re.DOTALL)
            paragraphs = []
            for p in p_matches:
                p_clean = clean_html(p)
                if len(p_clean) > 30 and not any(x in p_clean.lower() for x in ["copyright", "todos los derechos", "comercial:", "términos y condiciones"]):
                    paragraphs.append(p_clean)
            return "\n".join(paragraphs)
    except Exception as e:
        print(f"[WARNING] No se pudo obtener el cuerpo del artículo desde {url}: {e}")
    return ""

def analyze_news(title, description, link, fuente_nombre="Noticias San Juan"):
    title = clean_html(title)
    description = clean_html(description)
    text_to_search = (title + " " + description).lower()
    # Evitar falsos positivos de "fuego" en palabras que no refieren a un incendio (ej. matafuegos)
    text_to_search = text_to_search.replace("matafuegos", "").replace("matafuego", "")
    if any(black_word in text_to_search for black_word in BLACKLIST_KEYWORDS):
        return None
    detected_category = None
    if any(word in text_to_search for word in CONTEXT_WIND):
        for slug, keywords in WIND_MAPPING.items():
            if any(kw in text_to_search for kw in keywords):
                detected_category = slug
                break
    if not detected_category and any(word in text_to_search for word in CONTEXT_FIRE):
        is_firearm = "arma de fuego" in text_to_search or "armas de fuego" in text_to_search or "disparó" in text_to_search
        is_animal = "llamas" in text_to_search and any(a in text_to_search for a in ["animal", "aves", "guanaco", "fauna", "especie", "ejemplar"])
        if is_firearm or is_animal:
            pass
        else:
            detected_category = "incendio"
            for slug, keywords in FIRE_MAPPING.items():
                if any(kw in text_to_search for kw in keywords):
                    detected_category = slug
                    break
    if not detected_category and any(word in text_to_search for word in CONTEXT_ACCIDENT):
        for slug, keywords in ACCIDENT_MAPPING.items():
            if any(kw in text_to_search for kw in keywords):
                if slug == "vuelco":
                    # Palabras de contexto de vehículos o vías para validar que sea un vuelco real
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
                    
                    # Descartar frases metafóricas, de detenciones/robos o climáticas comunes
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
                    
                    if any(fp in text_to_search for fp in false_positives):
                        continue
                        
                    if not any(ctx in text_to_search for ctx in vuelco_context):
                        continue
                detected_category = slug
                break
    mentions_other_province = any(prov in text_to_search for prov in BLACKLIST_PROVINCIAS)
    mentions_local = any(loc.lower() in text_to_search for loc in LOCALIDADES) or any(dept.lower() in text_to_search for dept in DEPARTAMENTOS)
    if mentions_other_province and not mentions_local:
        return None
    res = geocoding_funnel(title)
    if res and not res[2]:
        lat, lon, is_approx = res
    else:
        full_res = geocoding_funnel(title + " " + description)
        if full_res:
            lat, lon, is_approx = full_res
        else:
            lat, lon, is_approx = None, None, True

    if (is_approx or lat is None) and link and link.startswith("http"):
        body_text = fetch_article_text(link)
        if body_text:
            text_to_search += " " + body_text.lower()
            deep_res = geocoding_funnel(body_text)
            if deep_res:
                d_lat, d_lon, d_is_approx = deep_res
                if not d_is_approx or (lat is None):
                    lat, lon, is_approx = d_lat, d_lon, d_is_approx

    if not detected_category:
        if any(word in text_to_search for word in CONTEXT_WIND):
            for slug, keywords in WIND_MAPPING.items():
                if any(kw in text_to_search for kw in keywords):
                    detected_category = slug
                    break
        if not detected_category and any(word in text_to_search for word in CONTEXT_FIRE):
            is_firearm = "arma de fuego" in text_to_search or "armas de fuego" in text_to_search or "disparó" in text_to_search
            is_animal = "llamas" in text_to_search and any(a in text_to_search for a in ["animal", "aves", "guanaco", "fauna", "especie", "ejemplar"])
            if not (is_firearm or is_animal):
                detected_category = "incendio"
                for slug, FIRE_MAPPING_kw in FIRE_MAPPING.items():
                    if any(kw in text_to_search for kw in FIRE_MAPPING_kw):
                        detected_category = slug
                        break
        if not detected_category and any(word in text_to_search for word in CONTEXT_ACCIDENT):
            for slug, keywords in ACCIDENT_MAPPING.items():
                if any(kw in text_to_search for kw in keywords):
                    if slug == "vuelco":
                        vuelco_context = ["auto", "automóvil", "automovil", "vehículo", "vehiculo", "coche", "camión", "camion", "camioneta", "colectivo", "micro", "ómnibus", "omnibus", "bus", "moto", "motocicleta", "motociclista", "ciclomotor", "rodado", "ciclista", "bicicleta", "bici", "peatón", "peatona", "transeúnte", "transeunte", "utilitario", "furgón", "furgon", "trafic", "ambulancia", "patrullero", "ruta", "calle", "avenida", "av.", "autopista", "carretera", "asfalto", "calzada", "banquina", "zanja", "cuneta", "bache", "semáforo", "semaforo", "esquina", "conductor", "conductores", "pasajero", "pasajeros", "volcadura", "tránsito", "transito", "vial"]
                        false_positives = ["vuelco inesperado", "vuelco en la causa", "vuelco en la investigacion", "vuelco en la investigación", "vuelco en el caso", "giro inesperado", "cayó detenido", "cayo detenido", "cayó preso", "cayo preso", "cayó la banda", "cayo la banda", "cayó una banda", "cayo una banda", "cayó por el robo", "cayo por el robo", "cayó por robo", "cayo por robo", "cayó por robar", "cayo por robar", "cayó in fraganti", "cayo in fraganti", "cayó con las manos", "cayo con las manos", "cayó tras", "cayo tras", "cayó acusado", "cayo acusado", "caída de granizo", "caida de granizo", "caída del cabello", "caida del cabello", "caída de las ventas", "caida de las ventas", "caída del consumo", "caida del consumo"]
                        if any(fp in text_to_search for fp in false_positives):
                            continue
                        if not any(ctx in text_to_search for ctx in vuelco_context):
                            continue
                    detected_category = slug
                    break

    if not detected_category or lat is None:
        return None

    is_fatal = any(kw in text_to_search for kw in FATAL_KEYWORDS)
    event_date = datetime.now()
    if "ayer" in text_to_search or "anoche" in text_to_search:
        from datetime import timedelta
        event_date = event_date - timedelta(days=1)
    return {
        "etiqueta": detected_category,
        "titulo": title[:250],
        "descripcion": description[:500] if description else "Sin descripción.",
        "latitud": lat,
        "longitud": lon,
        "is_approximate": is_approx,
        "is_fatal": is_fatal,
        "fuente_nombre": fuente_nombre,
        "fuente_url": link,
        "event_date": event_date.strftime("%Y-%m-%d %H:%M:%S"),
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
    for source in HTML_SOURCES:
        try:
            print(f"Scrapeando HTML: {source['medio']} ({source['url']})")
            response = session.get(source['url'], headers=HEADERS, timeout=15, verify=False)
            if response.status_code == 200:
                html_text = response.text
                matches = re.finditer(source['article_selector'], html_text, re.DOTALL)
                for match in matches:
                    link = match.group(1)
                    title = html.unescape(re.sub(r'<[^>]+>', '', match.group(2)).strip())
                    desc = match.group(3).strip() if len(match.groups()) > 2 else ""
                    desc = html.unescape(re.sub(r'<[^>]+>', '', desc))
                    if not link.startswith('http'):
                        from urllib.parse import urlparse
                        parsed_uri = urlparse(source['url'])
                        domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
                        link = domain + link
                    if link and is_url_processed(link):
                        print(f"[DB DUPLICADO] Saltando URL ya procesada: {link}")
                        continue
                    incident = analyze_news(title, desc, link, source['medio'])
                    if incident:
                        send_to_api(incident)
        except Exception as e:
            print(f"Error procesando HTML de {source['medio']}: {e}")

def scrape_rss():
    print(f"[{datetime.now()}] Iniciando barrido de RSS...")
    for feed_url in RSS_FEEDS:
        try:
            domain = feed_url.split('/')[2].replace('www.', '')
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
                    if link and is_url_processed(link):
                        print(f"[DB DUPLICADO] Saltando URL ya procesada: {link}")
                        continue
                    if title:
                        incident = analyze_news(title, desc, link, fuente_nombre)
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
            print(f"[{datetime.now()}] Esperando 1 hora para el próximo barrido...")
            time.sleep(3600)
    else:
        scrape_rss()
        scrape_html()
