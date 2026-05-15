import requests
import xml.etree.ElementTree as ET
import re
import urllib3
import time
from rss_scraper import RSS_FEEDS, HTML_SOURCES, HEADERS

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_rss():
    print("\n=== VERIFICANDO FEEDS RSS ===")
    for url in RSS_FEEDS:
        try:
            res = requests.get(url, headers=HEADERS, timeout=10, verify=False)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                items = root.findall('.//item')
                print(f"[OK] {url[:50]}... | Items encontrados: {len(items)}")
            else:
                print(f"[ERROR] {url} | Status: {res.status_code}")
        except Exception as e:
            print(f"[FALLA] {url} | Error: {str(e)[:50]}")

def check_html():
    print("\n=== VERIFICANDO FUENTES HTML ===")
    session = requests.Session()
    # Intentar calentar sesión para Diario Movil
    try:
        session.get("https://diariomovil.info/", headers=HEADERS, timeout=10, verify=False)
        time.sleep(1)
    except:
        pass

    for source in HTML_SOURCES:
        try:
            res = session.get(source['url'], headers=HEADERS, timeout=10, verify=False)
            if res.status_code == 200:
                matches = list(re.finditer(source['article_selector'], res.text, re.DOTALL))
                print(f"[OK] {source['medio']} | Noticias encontradas: {len(matches)}")
            else:
                print(f"[ERROR] {source['medio']} | Status: {res.status_code}")
        except Exception as e:
            print(f"[FALLA] {source['medio']} | Error: {str(e)[:50]}")

if __name__ == "__main__":
    check_rss()
    check_html()
