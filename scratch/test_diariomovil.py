import re

pattern = r'<article[^>]*class="[^"]*post[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>.*?<h[23][^>]*class="[^"]*titulo[^"]*"[^>]*>(.*?)</h[23]>.*?<div[^>]*class="[^"]*detalle[^"]*"[^>]*>(.*?)</div>'

print("[INFO] Reading scratch/diariomovil_sample.html...")
with open("scratch/diariomovil_sample.html", "r", encoding="utf-8") as f:
    html_text = f.read()

print(f"HTML Length: {len(html_text)}")

matches = list(re.finditer(pattern, html_text, re.DOTALL))
print(f"Matches found: {len(matches)}")

for i, match in enumerate(matches[:5]):
    link = match.group(1)
    title_raw = match.group(2)
    # clean HTML tags from title
    title = re.sub(r'<[^>]+>', '', title_raw).strip()
    desc_raw = match.group(3)
    desc = re.sub(r'<[^>]+>', '', desc_raw).strip()
    print(f"\n--- Match {i+1} ---")
    print(f"Link: {link}")
    print(f"Title: {title}")
    print(f"Desc: {desc}")
