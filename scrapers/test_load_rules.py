import sys
sys.path.insert(0, '.')
from load_rules import load_rules

rules = load_rules()
sources = rules["sources"]
print(f"Fuentes cargadas: {len(sources)}")
print()
for domain, cfg in sources.items():
    urls = len(cfg.get("scrape_urls", []))
    tipo = cfg["type"].upper()
    deep = cfg["deep_fetch"]
    print(f"  [{tipo}] {domain}  ({urls} URL/s)  deep_fetch={deep}")
