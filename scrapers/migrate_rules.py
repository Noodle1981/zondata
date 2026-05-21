import sqlite3
import json
import os
import sys

# Ensure paths are correct
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'zondata.db')
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'scraper_rules.json')

def migrate():
    # 1. Crear tabla si no existe
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraper_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL UNIQUE,
                rule_json TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"Error creando tabla: {e}")
        return

    # 2. Leer JSON base
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            rules = json.load(f)
    except Exception as e:
        print(f"Error leyendo JSON: {e}")
        return

    # 3. Insertar/Actualizar dominios en BD
    print("Migrando reglas a SQLite...")
    sources = rules.get("sources", {})
    for domain, rule_config in sources.items():
        rule_json_str = json.dumps(rule_config, ensure_ascii=False)
        try:
            cursor.execute("""
                INSERT INTO scraper_rules (domain, rule_json)
                VALUES (?, ?)
                ON CONFLICT(domain) DO UPDATE SET
                rule_json = excluded.rule_json,
                updated_at = CURRENT_TIMESTAMP
            """, (domain, rule_json_str))
            print(f" - [OK] {domain}")
        except Exception as e:
            print(f" - [ERROR] {domain}: {e}")

    conn.commit()
    conn.close()
    print("Migración completada.")

if __name__ == "__main__":
    migrate()
