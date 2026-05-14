import sys
import os

# Add scrapers directory to path
sys.path.append(os.path.abspath('scrapers'))

from rss_scraper import analyze_news

title = "Murió un motociclista bonaerense tras un violento accidente en Ruta 40"
description = "La víctima tenía unos 65 años y perdió la vida luego de caer de su moto en un tramo ubicado pasando Talacasto."
link = "https://canal4diario.com.ar/2026/05/13/murio-un-motociclista-bonaerense-tras-un-violento-accidente-en-ruta-40/"
fuente = "Canal 4 San Juan"

result = analyze_news(title, description, link, fuente)
print(f"Result: {result}")
