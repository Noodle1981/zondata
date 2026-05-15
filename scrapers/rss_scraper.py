import requests
import xml.etree.ElementTree as ET
import time
import sqlite3
import re
from datetime import datetime
import html
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración Global - Usamos Googlebot para maximizar compatibilidad y evitar bloqueos 403
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9',
    'Connection': 'keep-alive'
}

API_URL = "http://zondata.test/api/incidents"

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
        "article_selector": r'<a[^>]*class="[^"]*w-full[^"]*"[^>]*href="(/noticias/[^"]+)"[^>]*>.*?<h3[^>]*>(.*?)</h3>\s*(?:<h2[^>]*>)?(.*?)(?:</h2>)?\s*</a>',
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
CONTEXT_ACCIDENT = ["accidente", "siniestro", "tránsito", "transito", "choque", "vuelco", "vial", "falleció", "murió", "muerte", "víctima fatal", "deceso"]

# Palabras de contexto Incendios
CONTEXT_FIRE = ["incendio", "llamas", "bomberos", "quemó", "siniestro ígneo"]

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
    "choque": ["choque", "colisión", "impacto", "chocó", "impactó", "siniestro", "accidente", "vial"],
    "vuelco": ["vuelco", "volcó", "despistó", "cayó", "caída", "caida"],
    "atropello": ["atropelló", "embistió", "peatón", "arrolló", "moto", "motociclista"]
}

FIRE_MAPPING = {
    "incendio-vivienda": ["casa", "vivienda", "departamento", "edificio", "habitación"],
    "incendio-pastizales": ["pastizales", "campo", "lote", "baldío", "maleza"],
    "incendio-vehiculo": ["auto", "camioneta", "camión", "vehículo", "moto"]
}

# Configuración Geográfica (San Juan)
BOUNDING_BOX = [-32.7, -28.2, -70.6, -66.5]

DEPARTAMENTOS = [
    "Capital", "Rawson", "Rivadavia", "Chimbas", "Santa Lucía", 
    "Pocito", "Caucete", "Jáchal", "Albardón", "Sarmiento", 
    "25 de Mayo", "9 de Julio", "San Martín", "Angaco", 
    "Valle Fértil", "Iglesia", "Calingasta", "Ullum", "Zonda"
]

# Configuración de Base de Datos
DB_PATH = "database/database.sqlite"

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
            locs_with_context[loc_name] = f"{loc_name}, {dept_name}"
        
        conn.close()
        print(f"[INFO] Ubicaciones cargadas: {len(depts)} departamentos, {len(locs_with_context)} localidades.")
    except Exception as e:
        print(f"[ERROR] No se pudo cargar ubicaciones de la DB: {e}")
        depts = ["Capital", "Rawson", "Rivadavia", "Chimbas", "Santa Lucía", "Pocito", "Caucete", "Jáchal", "Albardón", "Sarmiento", "25 de Mayo", "9 de Julio", "San Martín", "Angaco", "Valle Fértil", "Iglesia", "Calingasta", "Ullum", "Zonda"]
        locs_with_context = {"Talacasto": "Talacasto, Ullum", "Media Agua": "Media Agua, Sarmiento"}
    
    return depts, locs_with_context

DEPARTAMENTOS, LOCALIDADES_CONTEXT = load_locations()
LOCALIDADES = list(LOCALIDADES_CONTEXT.keys())

print(f"[INFO] Scraper iniciado correctamente. Listo para procesar.")

BLACKLIST_PROVINCIAS = ["santa fe", "mendoza", "buenos aires", "córdoba", "cordoba", "san luis", "chile", "nacional", "rosario", "neuquén", "misionero", "corrientes"]

def clean_location_query(text):
    # Eliminar menciones a otras provincias para no confundir al geocoder
    cleaned = text.lower()
    for prov in BLACKLIST_PROVINCIAS:
        cleaned = cleaned.replace(prov, "")
    # Eliminar palabras que suelen acompañar procedencia
    noise = ["de buenos aires", "oriundo de", "proveniente de", "viajaba desde", "hacia", "rumbo a"]
    for word in noise:
        cleaned = cleaned.replace(word, "")
    return cleaned

BLACKLIST_KEYWORDS = [
    "alerta", "pronóstico", "pronostico", "precaución", "precaucion", "recomiendan", 
    "prevención", "prevencion", "llegaría", "llegaria", "internacional", "mundo",
    "escuela", "curso", "capacitación", "capacitacion", "proyecto", "campaña", 
    "historia de", "entrevista", "emicar", "clases", "inscripción", "inscripcion",
    "allanamiento", "detenido", "detenidos", "droga", "estupefacientes", "animales silvestres",
    "fauna", "caza ilegal", "secuestraron armas"
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

def get_hierarchical_context(text):
    """
    Busca contexto siguiendo la prioridad: Localidad -> Departamento -> Provincia
    """
    # 1. Prioridad: Localidad (Máxima precisión con su departamento)
    for loc, context in LOCALIDADES_CONTEXT.items():
        if loc.lower() in text.lower():
            return f"{context}, San Juan, Argentina"

    # 2. Prioridad: Departamento
    for dept in DEPARTAMENTOS:
        if dept.lower() in text.lower():
            return f"{dept}, San Juan, Argentina"
            
    return "San Juan, Argentina"

def geocoding_funnel(text):
    # Limpiar el texto de ruidos geográficos (Buenos Aires, etc) antes de buscar patrones
    text_clean = clean_location_query(text)
    
    patterns = [
        r"([Rr]uta\s+\d+)\s+(?:[Kk]m\.?|[Kk]il[óo]metro)\s+(\d+)",
        r"(?:[Cc]alle|[Aa]v\.?|[Aa]venida|[Rr]uta)?\s*([A-ZÁÉÍÓÚ][a-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-zñáéíóú]+)*)\s*(?:y|e|esquina|intersección\s+con|a\s+la\s+altura\s+de|frente\s+al)\s*(?:[Cc]alle|[Aa]v\.?|[Aa]venida|[Rr]uta)?\s*([A-ZÁÉÍÓÚ][a-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-zñáéíóú]+)*)",
        r"([Cc]alle|[Aa]v\.?|[Aa]venida|[Rr]uta)\s+([A-ZÁÉÍÓÚ][a-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-zñáéíóú]+)*)\s+(?:al|altura)\s+(\d+)",
        r"([Rr]uta\s+\d+)",
        r"([Aa]eropuerto|[Tt]erminal|[Cc]entro|[Pp]laza|[Bb]arrio|[Vv]illa)\s+([A-ZÁÉÍÓÚ][a-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-zñáéíóú]+)*)"
    ]
    
    local_context = get_hierarchical_context(text)
    
    for pattern in patterns:
        match = re.search(pattern, text_clean)
        if match:
            query = " ".join(filter(None, match.groups()))
            try:
                # Búsqueda ultra-específica con contexto local jerárquico
                location = geolocator.geocode(f"{query}, {local_context}", timeout=10)
                if location and is_within_bounds(location.latitude, location.longitude):
                    return location.latitude, location.longitude, False
            except:
                pass
    for loc in LOCALIDADES:
        if loc.lower() in text.lower():
            try:
                location = geolocator.geocode(f"{loc}, San Juan, Argentina", timeout=10)
                if location and is_within_bounds(location.latitude, location.longitude):
                    return location.latitude, location.longitude, True
            except:
                pass
    for dept in DEPARTAMENTOS:
        if dept.lower() in text.lower():
            try:
                location = geolocator.geocode(f"{dept}, San Juan, Argentina", timeout=10)
                if location and is_within_bounds(location.latitude, location.longitude):
                    return location.latitude, location.longitude, True
            except:
                pass
    if any(loc.lower() in text.lower() for loc in LOCALIDADES) or any(dept.lower() in text.lower() for dept in DEPARTAMENTOS) or "san juan" in text.lower():
        return -31.5375, -68.53639, True
    return None

def analyze_news(title, description, link, fuente_nombre="Noticias San Juan"):
    text_to_search = (title + " " + description).lower()
    if any(black_word in text_to_search for black_word in BLACKLIST_KEYWORDS):
        return None
    detected_category = None
    if any(word in text_to_search for word in CONTEXT_WIND):
        for slug, keywords in WIND_MAPPING.items():
            if any(kw in text_to_search for kw in keywords):
                detected_category = slug
                break
    if not detected_category and any(word in text_to_search for word in CONTEXT_ACCIDENT):
        for slug, keywords in ACCIDENT_MAPPING.items():
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
    mentions_other_province = any(prov in text_to_search for prov in BLACKLIST_PROVINCIAS)
    mentions_local = any(loc.lower() in text_to_search for loc in LOCALIDADES) or any(dept.lower() in text_to_search for dept in DEPARTAMENTOS)
    if mentions_other_province and not mentions_local:
        return None
    if not detected_category:
        return None
    res = geocoding_funnel(title)
    if res and not res[2]:
        lat, lon, is_approx = res
    else:
        full_res = geocoding_funnel(title + " " + description)
        if full_res:
            lat, lon, is_approx = full_res
        else:
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
    parser.add_argument('--daemon', action='store_true', help='Ejecutar en modo bucle infinito cada 30 minutos')
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
