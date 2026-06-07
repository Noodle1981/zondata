import requests
import xml.etree.ElementTree as ET
import html
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scrapers"))

from rss_scraper import HEADERS

url = "https://diariodecuyo.com.ar/rss/pages/policiales.xml"

print(f"[INFO] Fetching RSS: {url}")
try:
    res = requests.get(url, headers=HEADERS, timeout=10, verify=False)
    if res.status_code == 200:
        root = ET.fromstring(res.content)
        items = root.findall('.//item')
        print(f"Items found: {len(items)}")
        for i, item in enumerate(items[:5]):
            title_tag = item.find('title')
            pub_date_tag = item.find('pubDate')
            title = title_tag.text if title_tag is not None else ""
            pub_date_str = pub_date_tag.text if pub_date_tag is not None else ""
            print(f"\nItem {i+1}:")
            print(f"  Title: {title}")
            print(f"  pubDate: {pub_date_str}")
    else:
        print(f"Error: {res.status_code}")
except Exception as e:
    print(f"Exception: {e}")
