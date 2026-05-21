import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from rss_scraper import fetch_article_text, get_hierarchical_context, LOCALIDADES

print("Marquesado in LOCALIDADES:", "Marquesado" in LOCALIDADES)


url = "https://www.tiempodesanjuan.com/policiales/fuerte-choque-una-ciclista-y-colectivo-marquesado-la-mujer-tiene-muerte-cerebral-n430780"
body = fetch_article_text(url)
context = get_hierarchical_context(body)
print("Contexto jerárquico:", context)
