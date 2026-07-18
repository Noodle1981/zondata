import sys
sys.path.insert(0, '.')
from climate_enricher import enrich_incident_data

def test_enrichment():
    # Coordenadas de San Juan Capital
    lat = -31.5375
    lon = -68.5364
    
    # 1. Probar con una fecha histórica conocida en El Niño (ej: Enero 2024)
    date_el_nino = "2024-01-15 14:30:00"
    print(f"\n--- Probando enriquecimiento para {date_el_nino} (Debe ser El Niño) ---")
    data1 = enrich_incident_data(lat, lon, date_el_nino)
    print(f"Resultado: {data1}")
    assert data1["enso_phase"] == "niño", f"Fase ENSO incorrecta: {data1['enso_phase']}"
    assert data1["temp_c"] is not None, "Temperatura no obtenida"
    assert data1["wind_speed_kmh"] is not None, "Velocidad de viento no obtenida"
    
    # 2. Probar con una fecha histórica conocida en La Niña (ej: Enero 2022)
    date_la_nina = "2022-01-15 12:00:00"
    print(f"\n--- Probando enriquecimiento para {date_la_nina} (Debe ser La Niña) ---")
    data2 = enrich_incident_data(lat, lon, date_la_nina)
    print(f"Resultado: {data2}")
    assert data2["enso_phase"] == "niña", f"Fase ENSO incorrecta: {data2['enso_phase']}"
    assert data2["temp_c"] is not None, "Temperatura no obtenida"
    assert data2["wind_speed_kmh"] is not None, "Velocidad de viento no obtenida"

    print("\n[OK] Todas las pruebas de enriquecimiento climático pasaron exitosamente.")

if __name__ == "__main__":
    test_enrichment()
