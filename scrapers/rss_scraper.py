import requests
import xml.etree.ElementTree as ET
import time
import re
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración Global
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/xml,text/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5'
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
    "https://www.sanjuan8.com/rss",
    "https://canal4sanjuan.com.ar/feed/",
    "https://www.canal13sanjuan.com/rss",
    "https://nuevomundosj.com.ar/category/policiales/feed/",
    "https://www.telesoldiario.com/rss"
]

# Fuentes HTML (Sin RSS)
HTML_SOURCES = [
    {
        "url": "https://diariomovil.info/categoria/4/san-juan",
        "medio": "Diario Móvil",
        "article_selector": r'<div class="post">.*?<a[^>]*href="([^"]+)"[^>]*>.*?<h[23][^>]*>(.*?)</h[23]>.*?<div class="post__resumen">(.*?)</div>',
    },
    {
        "url": "https://www.0264noticias.com.ar/policiales",
        "medio": "0264Noticias",
        "article_selector": r'<a[^>]*class="[^"]*w-full[^"]*"[^>]*href="(/noticias/[^"]+)"[^>]*>.*?<h3[^>]*>(.*?)</h3>\s*(?:<h2[^>]*>)?(.*?)(?:</h2>)?\s*</a>',
    }
]

# Palabras de contexto Viento
CONTEXT_WIND = ["zonda", "viento sur", "ráfagas", "viento", "vientos"]

# Palabras de contexto Accidentes
CONTEXT_ACCIDENT = ["accidente", "siniestro", "tránsito", "transito", "choque", "vuelco", "vial"]

# Palabras de contexto Incendios
CONTEXT_FIRE = ["incendio", "llamas", "bomberos", "quemó", "siniestro ígneo"]
# Nota: Quitamos "fuego" solo porque suele venir de "arma de fuego" en policiales.
# Lo usaremos con más cuidado abajo.

FIRE_MAPPING = {
    "incendio": ["incendio", "llamas", "bomberos", "fuego"]
}

# Lista Negra de Provincias/Países para evitar fugas geográficas
BLACKLIST_PROVINCIAS = ["santa fe", "mendoza", "buenos aires", "córdoba", "cordoba", "san luis", "chile", "nacional", "rosario"]

# Configuración Geográfica (San Juan)
# Bounding Box: [min_lat, max_lat, min_lon, max_lon]
BOUNDING_BOX = [-32.7, -28.2, -70.6, -66.5]

DEPARTAMENTOS = [
    "Capital", "Rawson", "Rivadavia", "Chimbas", "Santa Lucía", 
    "Pocito", "Caucete", "Jáchal", "Albardón", "Sarmiento", 
    "25 de Mayo", "9 de Julio", "San Martín", "Angaco", 
    "Valle Fértil", "Iglesia", "Calingasta", "Ullum", "Zonda"
]

LOCALIDADES = [
    "Talacasto", "Media Agua", "Barreal", "Rodeo", "Las Flores", 
    "San José de Jáchal", "Jachal", "San Agustín", "Bermejo", 
    "Difunta Correa", "Niquivil", "Huaco", "Tudcum", "Pampa del Chañar",
    "Villa El Salvador", "Angualasto", "Tamberías", "Hilario", "Sondeo"
]

def is_within_bounds(lat, lon):
    return BOUNDING_BOX[0] <= lat <= BOUNDING_BOX[1] and BOUNDING_BOX[2] <= lon <= BOUNDING_BOX[3]

def get_local_context(text):
    # 1. Priorizar localidades específicas (Parajes)
    for loc in LOCALIDADES:
        if loc.lower() in text.lower():
            return f"{loc}, San Juan, Argentina"
            
    # 2. Buscar departamentos
    for dept in DEPARTAMENTOS:
        if dept.lower() in text.lower():
            return f"{dept}, San Juan, Argentina"
            
    return "San Juan, Argentina"

# Lista Negra
BLACKLIST_KEYWORDS = ["alerta", "pronóstico", "pronostico", "precaución", "precaucion", "recomiendan", "prevención", "prevencion", "llegaría", "llegaria", "internacional", "mundo"]

# Mapeos de categorías
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

# Mapeo de Incendios (Independiente)
FIRE_MAPPING = {
    "incendio-vivienda": ["casa", "vivienda", "departamento", "edificio", "habitación"],
    "incendio-pastizales": ["pastizales", "campo", "lote", "baldío", "maleza"],
    "incendio-vehiculo": ["auto", "camioneta", "camión", "vehículo", "moto"]
}

# Configuración Geocoding
geolocator = Nominatim(user_agent="zondata_scraper")
KM0_SAN_JUAN = (-31.5375, -68.5364) # Plaza 25 de Mayo

MUNICIPIOS_SJ = ["Capital", "Rawson", "Rivadavia", "Chimbas", "Santa Lucía", "Pocito", "Albardón", "Sarmiento", "25 de Mayo", "9 de Julio", "San Martín", "Angaco", "Ullum", "Zonda", "Calingasta", "Iglesia", "Jáchal", "Valle Fértil"]

def get_coordinates(query, attempts=3):
    try:
        full_query = query + ", San Juan, Argentina"
        location = geolocator.geocode(full_query)
        if location:
            return location.latitude, location.longitude, False
    except GeocoderTimedOut:
        if attempts > 0:
            return get_coordinates(query, attempts - 1)
    return None

def geocoding_funnel(text):
    # 1. Intentar con patrones específicos (KM, Cruce de calles, altura, etc)
    patterns = [
        # Patrón de Kilómetro (Muy preciso)
        r"([Rr]uta\s+\d+)\s+(?:[Kk]m\.?|[Kk]il[óo]metro)\s+(\d+)",
        # Patrón de Intersecciones
        r"([Cc]alle|[Aa]v\.?|[Aa]venida|[Rr]uta)\s+([A-ZÁÉÍÓÚ0-9][a-zñáéíóú0-9]+(?:\s+[A-ZÁÉÍÓÚ0-9][a-zñáéíóú0-9]+)*)\s+(?:y|e|intersección\s+con|a\s+la\s+altura\s+de|frente\s+al)\s+([A-ZÁÉÍÓÚ0-9][a-zñáéíóú0-9]+(?:\s+[A-ZÁÉÍÓÚ0-9][a-zñáéíóú0-9]+)*)",
        # Patrón de Rutas Genéricas
        r"([Rr]uta\s+\d+)",
        # Lugares de Referencia
        r"([Aa]eropuerto|[Tt]erminal|[Cc]entro|[Pp]laza)\s+([A-ZÁÉÍÓÚ0-9][a-zñáéíóú0-9]+(?:\s+[A-ZÁÉÍÓÚ0-9][a-zñáéíóú0-9]+)*)"
    ]
    
    local_context = get_local_context(text)
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            query = " ".join(filter(None, match.groups()))
            try:
                # Intentar búsqueda con el contexto local (Ej: "Ruta 40 km 70, Talacasto")
                location = geolocator.geocode(f"{query}, {local_context}", timeout=10)
                if location and is_within_bounds(location.latitude, location.longitude):
                    return location.latitude, location.longitude, False
            except:
                pass
    
    # 2. Si no hay patrón, buscar por parajes/localidades mencionadas (Aproximación por punto de interés)
    for loc in LOCALIDADES:
        if loc.lower() in text.lower():
            try:
                location = geolocator.geocode(f"{loc}, San Juan, Argentina", timeout=10)
                if location and is_within_bounds(location.latitude, location.longitude):
                    return location.latitude, location.longitude, True
            except:
                pass

    # 3. Departamentos (Aproximación por municipio)
    for dept in DEPARTAMENTOS:
        if dept.lower() in text.lower():
            try:
                location = geolocator.geocode(f"{dept}, San Juan, Argentina", timeout=10)
                if location and is_within_bounds(location.latitude, location.longitude):
                    return location.latitude, location.longitude, True
            except:
                pass

    # 4. Último recurso: KM 0
    return -31.5375, -68.53639, True

# Mapeo de nombres de medios
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
    
    # 3. Chequear si es un Incendio (Independiente)
    if not detected_category and any(word in text_to_search for word in CONTEXT_FIRE):
        # Exclusión específica: arma de fuego no es un incendio
        if "arma de fuego" in text_to_search or "disparó" in text_to_search:
            pass
        else:
            detected_category = "incendio"
            for slug, keywords in FIRE_MAPPING.items():
                if any(kw in text_to_search for kw in keywords):
                    detected_category = slug
                    break
    
    # 4. Validar que no sea una noticia de otra provincia (Fuga Geográfica)
    # Si menciona una provincia prohibida y NO menciona San Juan o un departamento, descartar.
    mentions_other_province = any(prov in text_to_search for prov in BLACKLIST_PROVINCIAS)
    mentions_local = any(loc.lower() in text_to_search for loc in LOCALIDADES) or any(dept.lower() in text_to_search for dept in DEPARTAMENTOS)
    
    if mentions_other_province and not mentions_local:
        return None
                
    if not detected_category:
        return None
        
    # Aplicar Embudo de Geolocalización
    # Intentar Nivel 1 en el título
    res = geocoding_funnel(title)
    if res and not res[2]: # Si encontró algo exacto
        lat, lon, is_approx = res
    else:
        # Si no, intentar en el texto completo
        lat, lon, is_approx = geocoding_funnel(title + " " + description)
    
    return {
        "etiqueta": detected_category,
        "titulo": title[:250],
        "descripcion": description[:500] if description else "Sin descripción.",
        "latitud": lat,
        "longitud": lon,
        "is_approximate": is_approx,
        "fuente_nombre": fuente_nombre,
        "fuente_url": link,
        "verificado": False
    }

def send_to_api(incident_data):
    try:
        res = requests.post(API_URL, json=incident_data, headers={'Accept': 'application/json', 'User-Agent': HEADERS['User-Agent']})
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
    for source in HTML_SOURCES:
        try:
            print(f"Scrapeando HTML: {source['medio']} ({source['url']})")
            response = requests.get(source['url'], headers=HEADERS, timeout=15, verify=False)
            if response.status_code == 200:
                html = response.text
                # Usar regex para extraer noticias del HTML (Estrategia ligera sin BeautifulSoup)
                matches = re.finditer(source['article_selector'], html, re.DOTALL)
                for match in matches:
                    link = match.group(1)
                    title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
                    desc = re.sub(r'<[^>]+>', '', match.group(3)).strip()
                    
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
            # Detectar nombre del medio
            domain = feed_url.split('/')[2].replace('www.', '')
            fuente_nombre = MEDIA_NAMES.get(domain, "Noticias San Juan")
            
            print(f"Leyendo: {fuente_nombre} ({feed_url})")
            response = requests.get(feed_url, headers=HEADERS, timeout=15, verify=False)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for item in root.findall('.//item'):
                    title_tag = item.find('title')
                    desc_tag = item.find('description')
                    
                    title = title_tag.text if title_tag is not None and title_tag.text else ''
                    desc = desc_tag.text if desc_tag is not None and desc_tag.text else ''
                    link = item.find('link').text if item.find('link') is not None else ''
                    
                    if title:
                        incident = analyze_news(title, desc, link, fuente_nombre)
                        if incident:
                            send_to_api(incident)
                            time.sleep(1) # Respetar rate limiting de Nominatim
                        else:
                            # Opcional: print(f"[IGNORADO] {title[:50]}...")
                            pass
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
            time.sleep(1800) # 30 minutos
    else:
        scrape_rss()
        scrape_html()
