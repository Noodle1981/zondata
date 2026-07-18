import sqlite3
import requests
import json
import os
import time

DB_PATH = 'database/database.sqlite'

def test_alerts():
    print("=" * 60)
    print("[TEST] PROBANDO SISTEMA DE ALERTAS (FASE 5)")
    print("=" * 60)

    # 1. Crear suscriptor de prueba en la Base de Datos
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Limpiar suscriptores anteriores de prueba
    cur.execute("DELETE FROM alert_subscribers WHERE email = 'test_alert@zondata.com'")
    conn.commit()

    # Insertar un suscriptor que quiere alertas de 'zonda' en el departamento 'Ullum' (ID 14)
    # y otro que quiere todas las alertas del departamento 'Zonda' (ID 15)
    print("[TEST] Creando suscriptores de prueba en la BD...")
    cur.execute('''
        INSERT INTO alert_subscribers (email, phone, department_id, phenomenon_type, is_active, created_at, updated_at)
        VALUES ('test_alert@zondata.com', '+549264555555', 14, 'zonda', 1, datetime('now'), datetime('now'))
    ''')
    cur.execute('''
        INSERT INTO alert_subscribers (email, phone, department_id, phenomenon_type, is_active, created_at, updated_at)
        VALUES ('test_general@zondata.com', '+549264777777', 15, NULL, 1, datetime('now'), datetime('now'))
    ''')
    conn.commit()
    conn.close()

    # 2. Enviar incidente vía POST al API local (Laravel)
    # Simulamos el ingreso de un incidente de tipo 'zonda' en 'Ullum'
    incident_data = {
        'etiqueta': 'viento-zonda',
        'titulo': 'Fuertes rafagas de viento Zonda provocaron incendios en Ullum',
        'descripcion': 'Varias dotaciones de bomberos trabajaron para sofocar las llamas avivadas por rafagas de Zonda en Ullum.',
        'latitud': -31.4730,
        'longitud': -68.7490,
        'is_approximate': True,
        'source': 'test',
        'location_type': 'GEOMETRIC_CENTER',
        'is_fatal': False,
        'fuente_nombre': 'Diario de Prueba',
        'fuente_url': 'https://prueba.com/incidente-zonda-ullum',
        'verificado': True,
        'event_date': '2026-07-17 14:00:00',
        'phenomenon_type': 'zonda',
        'wind_cause': True,
        'temp_c': 32.5,
        'humidity_pct': 12.0,
        'wind_speed_kmh': 65.4,
        'wind_direction_deg': 280,
        'precipitation_mm': 0.0,
        'weather_code': '0',
        'enso_phase': 'niño',
        'climate_enriched': True
    }

    print("\n[TEST] Enviando nuevo incidente de Zonda en Ullum via POST al servidor...")
    try:
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        resp = requests.post('http://127.0.0.1:8000/api/incidents', json=incident_data, headers=headers, timeout=5)
        print(f"[HTTP] Status: {resp.status_code}")
        print(f"[HTTP] Respuesta: {resp.json().get('message')}")
        
    except requests.exceptions.ConnectionError:
        print("[AVISO] El servidor Laravel local (127.0.0.1:8000) no esta activo.")
        print("[TEST] Simulando el disparo del Job a nivel de Artisan CLI...")
        
    # 3. Verificar si se generaron las alertas en el archivo alerts.log de Laravel
    alert_log_path = 'storage/logs/alerts.log'
    if os.path.exists(alert_log_path):
        print(f"\n[OK] Encontrado archivo de alertas en: {alert_log_path}")
        print("--- Ultimas lineas de storage/logs/alerts.log ---")
        with open(alert_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-5:]:
                print(line.strip())
        print("-------------------------------------------------")
    else:
        print(f"\n[AVISO] No se ha creado el archivo {alert_log_path} aun.")
        print("        Se creara cuando el Job SendClimateAlert sea procesado por Laravel.")

if __name__ == '__main__':
    test_alerts()
