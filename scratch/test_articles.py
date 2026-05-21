import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scrapers')))

import scrapers.rss_scraper as scraper
import requests

urls = [
    ("Parada colectivos", "https://www.diariodecuyo.com.ar/san-juan/rivadavia-ya-comenzo-construir-la-segunda-parada-colectivos-climatizada-n6567156"),
    ("Sismos", "https://www.diariodecuyo.com.ar/san-juan/dos-sismos-magnitud-35-y-31-sacudieron-san-juan-la-medianoche-n6145652")
]

for label, url in urls:
    print(f"\n=================== {label} ===================")
    print("URL:", url)
    body = scraper.fetch_article_text(url)
    print("Extracted body length:", len(body) if body else 0)
    
    # Let's inspect paragraphs containing any of the context words
    if body:
        paragraphs = body.split("\n")
        print("First 5 paragraphs extracted:")
        for p in paragraphs[:5]:
            print(f"- {p}")
            
        print("\nChecking context words in body:")
        for word in scraper.CONTEXT_ACCIDENT:
            if word in body.lower():
                print(f"  Matches CONTEXT_ACCIDENT: '{word}'")
        for word in scraper.CONTEXT_FIRE:
            if word in body.lower():
                print(f"  Matches CONTEXT_FIRE: '{word}'")
        for word in scraper.CONTEXT_WIND:
            if word in body.lower():
                print(f"  Matches CONTEXT_WIND: '{word}'")
                
        # Analyze it
        res = scraper.analyze_news(label, "Resumen", url)
        print("Analysis Result:", res)
