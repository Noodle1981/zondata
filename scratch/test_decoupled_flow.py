import sys
import os
import sqlite3
import shutil
from datetime import datetime

# Configurar paths
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "scrapers"))

import scrapers.rss_scraper as rss_scraper

# --- MONKEYPATCHING DE APIS PARA PRUEBA OFFLINE ---
# Mock de Gemini API
def mock_extract_gemini(title, description, body_text):
    print("[MOCK-GEMINI] Analizando noticia...")
    return {
        "location_query": "Calle San Miguel y Av Libertador, San Juan, Argentina",
        "is_approximate": False,
        "is_fatal": True,
        "category": "choque",
        "is_retrospective_or_historical": False,
        "victim_names": ["Pedro Gómez", "Juan Pérez"],
        "has_car": True,
        "has_pickup": False,
        "has_utility": False,
        "has_motorcycle": True,
        "has_truck": False,
        "has_bus": False,
        "has_pedestrian": False,
        "has_bicycle": False
    }
rss_scraper.extract_location_with_gemini = mock_extract_gemini

# Mock de Google Maps Geocoding
def mock_resolve_geocode(query, is_approx):
    print(f"[MOCK-GOOGLE] Geocodificando: '{query}'")
    return (-31.5375, -68.5364, False, 'google', 'ROOFTOP')
rss_scraper.resolve_geocode = mock_resolve_geocode

# Mock de send_to_api para no mandar datos reales a la API de Laravel
def mock_send_to_api(incident_data):
    print(f"[MOCK-API] Enviando incidente a Laravel:")
    print(f"  Título: '{incident_data['titulo']}'")
    print(f"  Categoría: '{incident_data['etiqueta']}'")
    print(f"  Víctimas: '{incident_data.get('victim_names')}'")
    print(f"  Auto: {incident_data.get('has_car')} | Moto: {incident_data.get('has_motorcycle')}")
rss_scraper.send_to_api = mock_send_to_api


def setup_test_db():
    print("[TEST] Creando base de datos temporal para pruebas...")
    # Crear una copia de respaldo si existe la original para no modificarla en pruebas destructivas
    db_path = rss_scraper.DB_PATH
    if os.path.exists(db_path):
        shutil.copyfile(db_path, db_path + ".bak")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Asegurar que las tablas existan
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            body TEXT,
            source_name TEXT,
            source_url TEXT UNIQUE,
            publish_date TEXT,
            status TEXT DEFAULT 'queued',
            error_message TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    # Limpiar registros previos de prueba
    cursor.execute("DELETE FROM raw_articles")
    cursor.execute("DELETE FROM content_hash_cache")
    conn.commit()
    conn.close()

def seed_test_data():
    print("[TEST] Insertando datos de prueba en la cola...")
    conn = sqlite3.connect(rss_scraper.DB_PATH)
    cursor = conn.cursor()
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Noticia que debería pasar el pre-filtro de Python y procesarse con Gemini
    cursor.execute("""
        INSERT INTO raw_articles 
        (title, description, body, source_name, source_url, publish_date, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 'queued', ?, ?)
    """, (
        "Choque fatal en Rivadavia: murio el motociclista",
        "Un tremendo siniestro vial ocurrio esta madrugada sobre la Avenida Libertador.",
        "El motociclista colisiono contra un auto y fallecio en el acto debido al fuerte impacto.",
        "Diario de Cuyo",
        "https://www.diariodecuyo.com.ar/policiales/choque-fatal-rivadavia",
        now_str,
        now_str,
        now_str
    ))
    
    # 2. Noticia que NO es incidente y debería ser IGNORADA de inmediato por las reglas locales de Python
    cursor.execute("""
        INSERT INTO raw_articles 
        (title, description, body, source_name, source_url, publish_date, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 'queued', ?, ?)
    """, (
        "Rivadavia ya comenzo a construir la segunda parada de colectivos",
        "Las obras viales avanzan en la zona oeste para mejorar las garitas de colectivos.",
        "El intendente visito la construccion de la nueva parada de colectivo que estara lista a fin de mes.",
        "Tiempo de San Juan",
        "https://www.tiempodesanjuan.com/sanjuan/parada-colectivo",
        now_str,
        now_str,
        now_str
    ))
    
    conn.commit()
    conn.close()

def run_verification():
    print("\n--- INICIANDO VERIFICACIÓN DE PROCESAMIENTO ---")
    rss_scraper.process_queued_articles()
    
    print("\n--- RESULTADOS EN LA BASE DE DATOS ---")
    conn = sqlite3.connect(rss_scraper.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, status, error_message FROM raw_articles")
    rows = cursor.fetchall()
    
    for row in rows:
        art_id, title, status, err = row
        print(f"ID {art_id} | Status: {status} | '{title[:40]}...' | Error: {err}")
        
    conn.close()
    
    # Restaurar base de datos original si existía respaldo
    db_path = rss_scraper.DB_PATH
    if os.path.exists(db_path + ".bak"):
        os.remove(db_path)
        os.rename(db_path + ".bak", db_path)
        print("[TEST] Base de datos original restaurada.")

if __name__ == "__main__":
    setup_test_db()
    seed_test_data()
    run_verification()
