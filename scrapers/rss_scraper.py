import requests
import xml.etree.ElementTree as ET
import time
import re
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "http://zondata.test/api/incidents"
RSS_FEEDS = [
    "https://diariodecuyo.com.ar/rss/rss.xml",
    "https://www.tiempodesanjuan.com/rss/",
    "https://www.diariohuarpe.com/feed",
    "https://www.nuevodiariosanjuan.com/feed",
    "https://www.diariomovil.info/feed",
    "https://www.diarioelzonda.com.ar/feed",
    "https://www.sanjuan8.com/rss"
]

# Palabras de contexto Viento
CONTEXT_WIND = ["zonda", "viento sur", "ráfagas", "viento", "vientos"]

# Palabras de contexto Accidentes
CONTEXT_ACCIDENT = ["accidente", "siniestro", "tránsito", "transito", "choque", "vuelco", "vial"]

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
    "choque": ["choque", "colisión", "impacto", "chocó", "impactó", "siniestro"],
    "vuelco": ["vuelco", "volcó", "despistó"],
    "atropello": ["atropelló", "embistió", "peatón", "arrolló"]
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
    # Nivel 1: Búsqueda Directa (Intersecciones)
    # Patrones comunes: "Calle X e Y", "Calle X y Calle Y", "Avenida X y Calle Y"
    # Ahora más flexible con los nombres de las calles
    patterns = [
        r"([Cc]alle|[Aa]v\.?|[Aa]venida)\s+([A-ZÁÉÍÓÚ][a-zñáéíóú0-9]+(?:\s+[A-ZÁÉÍÓÚ][a-zñáéíóú0-9]+)*)\s+(?:y|e|intersección\s+con)\s+([A-ZÁÉÍÓÚ][a-zñáéíóú0-9]+(?:\s+[A-ZÁÉÍÓÚ][a-zñáéíóú0-9]+)*)",
        r"esquina\s+de\s+([A-ZÁÉÍÓÚ][a-zñáéíóú0-9]+(?:\s+[A-ZÁÉÍÓÚ][a-zñáéíóú0-9]+)*)\s+y\s+([A-ZÁÉÍÓÚ][a-zñáéíóú0-9]+(?:\s+[A-ZÁÉÍÓÚ][a-zñáéíóú0-9]+)*)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            query = f"{match.group(1)} {match.group(2)} y {match.group(3)}" if len(match.groups()) == 3 else f"{match.group(1)} y {match.group(2)}"
            coords = get_coordinates(query)
            if coords:
                return coords # (lat, lon, is_approximate=False)

    # Nivel 3: Aproximación Zonal (Municipios)
    for muni in MUNICIPIOS_SJ:
        if muni.lower() in text.lower():
            coords = get_coordinates(muni)
            if coords:
                return coords[0], coords[1], True # (lat, lon, is_approximate=True)

    # Nivel 4: Último Recurso (KM 0)
    return KM0_SAN_JUAN[0], KM0_SAN_JUAN[1], True

def analyze_news(title, description, link):
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
        "fuente_nombre": "RSS Noticias San Juan",
        "fuente_url": link,
        "verificado": False
    }

def send_to_api(incident_data):
    try:
        res = requests.post(API_URL, json=incident_data, headers={'Accept': 'application/json'})
        if res.status_code == 201:
            print(f"[OK] Incidente guardado: {incident_data['etiqueta']} - {incident_data['titulo']}")
        elif res.status_code == 200:
            print(f"[DUPLICADO] {incident_data['titulo']}")
        else:
            print(f"[ERROR] {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[CONEXION FALLIDA] No se pudo enviar a la API: {e}")

def scrape_rss():
    print(f"[{datetime.now()}] Iniciando barrido de RSS...")
    for feed_url in RSS_FEEDS:
        try:
            print(f"Leyendo: {feed_url}")
            response = requests.get(feed_url, timeout=10, verify=False)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for item in root.findall('.//item'):
                    title = item.find('title').text if item.find('title') is not None else ''
                    desc = item.find('description').text if item.find('description') is not None else ''
                    link = item.find('link').text if item.find('link') is not None else ''
                    
                    if title:
                        incident = analyze_news(title, desc, link)
                        if incident:
                            send_to_api(incident)
                            time.sleep(1) # Respetar rate limiting de Nominatim
        except Exception as e:
            print(f"Error procesando el feed {feed_url}: {e}")

if __name__ == "__main__":
    scrape_rss()
