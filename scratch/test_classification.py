import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scrapers.rss_scraper import analyze_news

title1 = "Fuerte choque en Ruta 40: un auto termino destrozado tras impactar contra una camioneta | Diario La Provincia San Juan"
desc1 = "Sucedio este mediodia en el tramo entre Calles 9 y 10."
link1 = "https://diariolaprovinciasj.com/policiales/fuerte-choque-en-ruta-40-un-auto-termino-destrozado-tras-impactar-contra-una-camioneta-340183/"

res1 = analyze_news(title1, desc1, link1, "Diario La Provincia")
print("--- TEST CASE 1: Pocito (Calle 9 y 10) ---")
if res1:
    print(f"COORDENADAS: ({res1['latitud']}, {res1['longitud']})")
    print(f"APROXIMADO: {res1['is_approximate']}")
else:
    print("No se pudo clasificar o geolocalizar el primer caso.")

title2 = "Peligroso incendio en Sarmiento: una Trafic terminó calcinada en un garage | 0264Noticias"
desc2 = "El siniestro ocurrió durante la madrugada en el barrio Virgen de Luján, en Media Agua. Bomberos lograron controlar las llamas y no hubo personas heridas, aunque el vehículo sufrió importantes daños"
link2 = "https://www.0264noticias.com.ar/noticias/2026/05/18/94476-peligroso-incendio-en-sarmiento-una-trafic-termino-calcinada-en-un-garage"

res2 = analyze_news(title2, desc2, link2, "0264Noticias")
print("\n--- TEST CASE 2: Incendio en Sarmiento (Media Agua) ---")
if res2:
    print(f"TITULO: {res2['titulo']}")
    print(f"COORDENADAS: ({res2['latitud']}, {res2['longitud']})")
    print(f"APROXIMADO: {res2['is_approximate']}")
else:
    print("No se pudo clasificar o geolocalizar el segundo caso.")

title3 = "Jáchal despide a Carlos Páez, el futbolista que murió en un choque contra un árbol | 0264Noticias"
desc3 = "El hombre falleció este viernes tras chocar contra un árbol en una zona rural de Pampa del Chañar. En redes sociales, allegados compartieron mensajes de despedida y recordaron su paso por el fútbol local."
link3 = "https://www.0264noticias.com.ar/noticias/2026/05/15/94203-jachal-despide-a-carlos-paez-el-futbolista-que-murio-en-un-choque-contra-un-arbol"

res3 = analyze_news(title3, desc3, link3, "0264Noticias")
print("\n--- TEST CASE 3: Choque contra árbol en Jáchal (Carlos Páez) ---")
if res3:
    print(f"TITULO: {res3['titulo']}")
    print(f"COORDENADAS: ({res3['latitud']}, {res3['longitud']})")
    print(f"APROXIMADO: {res3['is_approximate']}")
else:
    print("No se pudo clasificar o geolocalizar el tercer caso.")
