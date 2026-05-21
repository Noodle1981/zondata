import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scrapers')))

import scrapers.rss_scraper as scraper

def mock_resolve_geocode(query_str, is_approx):
    print(f"MOCK RESOLVE_GEOCODE CALLED WITH: '{query_str}'")
    return None

scraper.resolve_geocode = mock_resolve_geocode

test_text = "Trabajar & Producir"

print("--- Running geocoding_funnel for Trabajar & Producir ---")
res = scraper.geocoding_funnel(test_text)
print("Result:", res)
