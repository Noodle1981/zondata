import requests
import xml.etree.ElementTree as ET
import re
import urllib3
import time
from rss_scraper import HEADERS, get_headers
from load_rules import load_rules, get_source_rule

RULES = load_rules()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_rss():
    print("\n=== VERIFICANDO FEEDS RSS ===")
    for domain, source_config in RULES["sources"].items():
        rule = get_source_rule(RULES, domain)
        if rule["type"] != "rss":
            continue
        for url in rule.get("scrape_urls", []):
            try:
                res = requests.get(url, headers=get_headers(url), timeout=10, verify=False)
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
        session.get("https://diariomovil.info/", headers=get_headers("https://diariomovil.info/"), timeout=10, verify=False)
        time.sleep(1)
    except:
        pass

    for domain, source_config in RULES["sources"].items():
        rule = get_source_rule(RULES, domain)
        if rule["type"] != "html":
            continue
        for url in rule.get("scrape_urls", []):
            try:
                res = session.get(url, headers=get_headers(url), timeout=10, verify=False)
                if res.status_code == 200:
                    matches = list(re.finditer(rule['article_selector'], res.text, re.DOTALL))
                    print(f"[OK] {domain} | Noticias encontradas: {len(matches)}")
                else:
                    print(f"[ERROR] {domain} | Status: {res.status_code}")
            except Exception as e:
                print(f"[FALLA] {domain} | Error: {str(e)[:50]}")

if __name__ == "__main__":
    check_rss()
    check_html()
