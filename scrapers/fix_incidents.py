import sqlite3
import os
import requests
from rss_scraper import geocoding_funnel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "database.sqlite")

def fix_incident(incident_id=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if incident_id:
        cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
    else:
        # Re-evaluar los que no tienen localidad ni departamento pero están en San Juan
        cursor.execute("SELECT * FROM incidents WHERE locality_id IS NULL AND department_id IS NULL")
        
    incidents = cursor.fetchall()
    
    for inc in incidents:
        text = f"{inc['title']} {inc['description']}"
        print(f"Evaluando: {inc['id']} - {inc['title']}")
        lat, lon, is_approx = geocoding_funnel(text)
        
        if lat and lon:
            print(f"  Nuevas coordenadas: {lat}, {lon} (Approx: {is_approx})")
            cursor.execute("""
                UPDATE incidents 
                SET latitude = ?, longitude = ?, is_approximate = ? 
                WHERE id = ?
            """, (lat, lon, int(is_approx), inc['id']))
            conn.commit()
            print("  [OK] Incidente actualizado.")
        else:
            print("  [FALLO] No se encontraron coordenadas mejores.")

    conn.close()

if __name__ == "__main__":
    print("Reparando incidente 27...")
    fix_incident(27)
