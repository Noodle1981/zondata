import sys
import os

# Add scrapers directory to path
sys.path.append(os.path.abspath('scrapers'))

from rss_scraper import analyze_news

title = "Caos vehicular en Ruta 20: una frenada provocó un choque múltiple frente al Aeropuerto"
description = "Un fuerte siniestro vial se produjo en la mañana de este miércoles sobre la Ruta 20, a metros del Aeropuerto de San Juan. Hubo varios vehículos involucrados."
link = "https://www.tiempodesanjuan.com/policiales/caos-vehicular-ruta-20-una-frenada-provoco-un-choque-multiple-frente-al-aeropuerto-n430107"
fuente = "Tiempo de San Juan"

result = analyze_news(title, description, link, fuente)
print(f"Result: {result}")
