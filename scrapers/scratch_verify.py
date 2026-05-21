import sys
import os

# Asegurar que el directorio scraper está en el path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rss_scraper import analyze_news, resolve_geocode, get_cached_coords

urls = [
    {
        "url": "https://www.tiempodesanjuan.com/policiales/fuerte-choque-una-ciclista-y-colectivo-marquesado-la-mujer-tiene-muerte-cerebral-n430780",
        "title": "Fuerte choque entre una ciclista y colectivo en Marquesado: la mujer tiene muerte cerebral",
        "desc": "El siniestro ocurrió este miércoles en Rivadavia. La ciclista, de 54 años, fue trasladada al Hospital Rawson.",
        "fuente": "Tiempo de San Juan"
    },
    {
        "url": "https://www.0264noticias.com.ar/noticias/2026/05/20/94878-una-ciclista-de-54-anos-termino-gravemente-herida-tras-chocar-contra-un-colectivo-de-la-red-tulum-en-rivadavia-tiene-muerte-cerebral",
        "title": "Una ciclista de 54 años terminó gravemente herida tras chocar contra un colectivo de la Red Tulum en Rivadavia: tiene muerte cerebral",
        "desc": "",
        "fuente": "0264Noticias"
    }
]

print("=== VERIFICACIÓN DE INCIDENTES ===")
for item in urls:
    print(f"\nAnalizando: {item['fuente']}")
    # Probando explícitamente el deep fetch para depurar
    from rss_scraper import fetch_article_text, geocoding_funnel
    from load_rules import load_rules, get_source_rule
    
    # Extraer el dominio base de la url
    from urllib.parse import urlparse
    domain = urlparse(item['url']).netloc.replace("www.", "")
    rules = load_rules()
    rule = get_source_rule(rules, domain)

    body = fetch_article_text(item['url'])
    print(f"[{item['fuente']}] Longitud del Body extraído: {len(body)}")
    if "Gal" in body or "Soldado" in body:
        print("Las calles SÍ están en el body.")
    else:
        print("Las calles NO se extrajeron en el body.")
    
    deep_res = geocoding_funnel(body, rule)
    print(f"Deep Res directo: {deep_res}")

    res = analyze_news(item['title'], item['desc'], item['url'], item['fuente'], rule)
    if res:
        print(f"[{item['fuente']}] Coordenadas Finales: {res['latitud']}, {res['longitud']} (Approx: {res['is_approximate']})")
    else:
        print(f"[{item['fuente']}] No se generó incidente o no se detectó categoría.")
