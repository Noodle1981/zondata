import requests
import xml.etree.ElementTree as ET
import time
from datetime import datetime

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
CONTEXT_WIND = ["zonda", "viento sur", "ráfagas", "viento"]

# Palabras de contexto Accidentes
CONTEXT_ACCIDENT = ["accidente", "siniestro", "tránsito", "transito", "choque", "vuelco"]

# Lista Negra: Si dice esto, es pronóstico/preventivo y se ignora
BLACKLIST_KEYWORDS = ["alerta", "pronóstico", "pronostico", "precaución", "precaucion", "recomiendan", "prevención", "prevencion", "llegaría", "llegaria", "internacional", "mundo"]

# Mapeo de Viento
WIND_MAPPING = {
    "arboles": ["árbol", "arbol", "ramas", "caída de árboles", "caida de arbol"],
    "corte": ["corte de luz", "sin luz", "energía san juan", "transformador", "cables cortados"],
    "incendio": ["incendio", "fuego", "bomberos", "pastizales"],
    "techo": ["techo", "voladura", "chapa"]
}

# Mapeo de Accidentes
ACCIDENT_MAPPING = {
    "choque": ["choque", "colisión", "impacto", "chocó", "impactó"],
    "vuelco": ["vuelco", "volcó", "despistó"],
    "atropello": ["atropelló", "embistió", "peatón", "arrolló"]
}

def analyze_news(title, description, link):
    text_to_search = (title + " " + description).lower()
    
    # 0. Lista Negra
    if any(black_word in text_to_search for black_word in BLACKLIST_KEYWORDS):
        return None

    detected_category = None
    
    # 1. Chequear si es un incidente de Viento
    if any(word in text_to_search for word in CONTEXT_WIND):
        for slug, keywords in WIND_MAPPING.items():
            if any(kw in text_to_search for kw in keywords):
                detected_category = slug
                break

    # 2. Si no es viento, chequear si es Accidente de Tránsito
    if not detected_category and any(word in text_to_search for word in CONTEXT_ACCIDENT):
        for slug, keywords in ACCIDENT_MAPPING.items():
            if any(kw in text_to_search for kw in keywords):
                detected_category = slug
                break
                
    if not detected_category:
        return None
        
    # En una implementación real usaríamos una API de Geocoding (ej. OpenStreetMap Nominatim)
    # Por ahora, usamos coordenadas aproximadas en San Juan Capital/Gran San Juan
    # para demostrar que funciona en el mapa
    import random
    lat = -31.5375 + random.uniform(-0.05, 0.05)
    lon = -68.5364 + random.uniform(-0.05, 0.05)
    
    return {
        "etiqueta": detected_category, # Enviamos el slug y el backend creará/usará la categoría
        "titulo": title[:250],
        "descripcion": description[:500] if description else "Sin descripción.",
        "latitud": lat,
        "longitud": lon,
        "fuente_nombre": "RSS Noticias San Juan",
        "fuente_url": link,
        "verificado": False
    }

def send_to_api(incident_data):
    try:
        res = requests.post(API_URL, json=incident_data, headers={'Accept': 'application/json'})
        if res.status_code == 201:
            print(f"[OK] Incidente guardado: {incident_data['etiqueta']} - {incident_data['titulo']}")
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
                # Parsear items dependiendo del formato (normalmente channel/item)
                for item in root.findall('.//item'):
                    title = item.find('title').text if item.find('title') is not None else ''
                    desc = item.find('description').text if item.find('description') is not None else ''
                    link = item.find('link').text if item.find('link') is not None else ''
                    
                    if title:
                        incident = analyze_news(title, desc, link)
                        if incident:
                            send_to_api(incident)
        except Exception as e:
            print(f"Error procesando el feed {feed_url}: {e}")

if __name__ == "__main__":
    scrape_rss()
