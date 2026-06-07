import sqlite3
import json

conn = sqlite3.connect('database/database.sqlite')
cursor = conn.cursor()

print("=== ÚLTIMOS INCIDENTES REGISTRADOS EN LA DB ===")
cursor.execute("""
    SELECT id, title, event_date, latitude, longitude, is_approximate, is_fatal, status, category_id, road_type, road_name
    FROM incidents
    ORDER BY id DESC
    LIMIT 10;
""")

rows = cursor.fetchall()
for r in rows:
    print(f"\nID: {r[0]}")
    print(f"  Título: {r[1]}")
    print(f"  Fecha: {r[2]}")
    print(f"  Coords: ({r[3]}, {r[4]})")
    print(f"  Aproximada: {bool(r[5])} | Fatal: {bool(r[6])} | Status: {r[7]}")
    print(f"  Categoría ID: {r[8]} | Vía: {r[9]} ({r[10]})")

conn.close()
