import json
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Leer de la base de datos principal de Laravel (database/database.sqlite)
# Las reglas se gestionan desde /admin y se restauran con el ScraperSourceSeeder.
DB_PATH = os.path.join(BASE_DIR, '..', 'database', 'database.sqlite')

def load_rules():
    """
    Carga las reglas del scraper desde la tabla scraper_sources de la base de datos principal.
    Retorna el diccionario con la estructura {"sources": {...}, "global": {...}}.
    """
    rules = {
        "sources": {},
        "global": {
            "fallback_context": "San Juan, Argentina",
            "duplicate_check": True,
            "deep_fetch": True
        }
    }

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scraper_sources'")
        if not cursor.fetchone():
            print("[WARN] La tabla scraper_sources no existe. Ejecuta: php artisan migrate --seed")
            conn.close()
            return rules

        cursor.execute("""
            SELECT domain, name, type, scrape_urls, sanitize_exclusions,
                   ignore_terms, article_selector, fallback_context,
                   custom_context, deep_fetch, duplicate_check, priority
            FROM scraper_sources
            WHERE active = 1
            ORDER BY priority DESC
        """)

        for row in cursor.fetchall():
            (domain, name, src_type, scrape_urls_json, sanitize_json,
             ignore_json, article_selector, fallback_ctx,
             custom_ctx, deep_fetch, duplicate_check, priority) = row

            rule = {
                "type":             src_type,
                "scrape_urls":      json.loads(scrape_urls_json) if scrape_urls_json else [],
                "deep_fetch":       bool(deep_fetch),
                "duplicate_check":  bool(duplicate_check),
                "fallback_context": fallback_ctx or "San Juan, Argentina",
                "priority":         priority or 1,
            }

            if sanitize_json:
                parsed = json.loads(sanitize_json)
                if parsed:
                    rule["sanitize_exclusions"] = parsed

            if ignore_json:
                parsed = json.loads(ignore_json)
                if parsed:
                    rule["ignore_terms"] = parsed

            if article_selector:
                rule["article_selector"] = article_selector

            if custom_ctx:
                rule["custom_context"] = custom_ctx

            rules["sources"][domain] = rule

        conn.close()
        print(f"[INFO] {len(rules['sources'])} fuentes cargadas desde scraper_sources.")

    except Exception as e:
        print(f"[WARN] No se pudo leer reglas desde scraper_sources: {e}")

    return rules


def get_source_rule(rules, domain):
    """
    Obtiene la configuración consolidada para un dominio específico,
    haciendo fallbacks a los valores globales si no se definen.
    """
    source_cfg = rules["sources"].get(domain, {})
    global_cfg  = rules.get("global", {})

    return {
        "type":               source_cfg.get("type", "html"),
        "scrape_urls":        source_cfg.get("scrape_urls", []),
        "article_selector":   source_cfg.get("article_selector", ""),
        "sanitize_exclusions":source_cfg.get("sanitize_exclusions", []),
        "ignore_terms":       source_cfg.get("ignore_terms", []),
        "priority":           source_cfg.get("priority", 1),
        "custom_context":     source_cfg.get("custom_context"),
        "hierarchy_overrides":source_cfg.get("hierarchy_overrides", {}),
        "deep_fetch":         source_cfg.get("deep_fetch", global_cfg.get("deep_fetch", True)),
        "duplicate_check":    source_cfg.get("duplicate_check", global_cfg.get("duplicate_check", True)),
        "fallback_context":   source_cfg.get("fallback_context", global_cfg.get("fallback_context", "San Juan, Argentina")),
    }
