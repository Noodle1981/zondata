import re
import requests

url_sismos = "https://www.diariodecuyo.com.ar/san-juan/dos-sismos-magnitud-35-y-31-sacudieron-san-juan-la-medianoche-n6145652"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9',
    'Connection': 'keep-alive'
}

print("Fetching Sismos URL...")
r = requests.get(url_sismos, headers=HEADERS, verify=False)
html = r.text

print("\n--- Original Extraction (first 20 paragraphs) ---")
p_matches = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
print(f"Total <p> tags found: {len(p_matches)}")
for idx, p in enumerate(p_matches):
    p_clean = re.sub(r'<[^>]+>', '', p)
    p_clean = re.sub(r'\s+', ' ', p_clean).strip()
    if len(p_clean) > 0:
        print(f"{idx+1}: {p_clean[:120]}...")


