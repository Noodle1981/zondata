import sys
import os
import json

# Agregar el directorio raíz y scrapers al path para poder importar
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "scrapers"))


from scrapers.rss_scraper import analyze_news

# Artículo de prueba
title = "Nuevo vuelco e incendio de un auto en Ruta 40 y Calle 15, Pocito"
description = "Un vehículo volcó esta madrugada e inmediatamente comenzó a prenderse fuego. Personal de bomberos extinguió las llamas. Murió el conductor del rodado."
link = "https://www.diariodecuyo.com.ar/policiales/nuevo-vuelco-e-incendio-de-un-auto-en-pocito-2"

print("[RUN] Iniciando análisis de prueba con analyze_news...")
result = analyze_news(
    title=title,
    description=description,
    link=link,
    fuente_nombre="Diario de Cuyo",
    pub_date_str="Sat, 06 Jun 2026 12:00:00 -0300"
)

if result:
    print("\n[SUCCESS] Resultado del análisis:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
else:
    print("\n[FAILED] El análisis retornó None (posiblemente descartado por filtros o error).")
