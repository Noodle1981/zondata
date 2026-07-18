import sys
import os

# Set environment variable before importing rss_scraper
os.environ["ENABLE_ACCIDENT_SCRAPING"] = "false"

sys.path.insert(0, '.')
from rss_scraper import CONTEXT_WIND, CONTEXT_FIRE, CONTEXT_ACCIDENT, classify_article_with_python_rules, get_env_variable

print(f"ENABLE_ACCIDENT_SCRAPING set to: {get_env_variable('ENABLE_ACCIDENT_SCRAPING')}")
print(f"Keywords viento   : {len(CONTEXT_WIND)}")
print(f"Keywords incendio : {len(CONTEXT_FIRE)}")

tests = [
    # (titulo, cuerpo, deberia_pasar_categoria)
    # Deben pasar (clima e incendios)
    ("Zonda: volo un techo y dejo sin luz a familias", "", "zonda"),
    ("Arbol caido interrumpio el transito en Avenida Libertador", "", "arboles-caidos"),
    ("Bomberos controlaron un incendio en pastizales de Pocito", "", "incendio-pastizales"),
    ("Se incendio una camioneta en plena Ruta 20", "", "incendio-vehiculo"),
    ("Vientos fuertes causaron danos en varias zonas de San Juan", "", "zonda"),
    ("Rafagas de viento derribaron arboles en Caucete", "", "arboles-caidos"),
    # Deben fallar/ser rechazados (accidentes viales puros sin viento/clima)
    ("Choque fatal en Rivadavia: murio el motociclista", "", None),
    ("Vuelco en Ruta 40: dos heridos graves", "", None),
    ("Atropello a un peatón y se dio a la fuga", "", None),
    ("Colision entre un auto y una moto en Capital", "", None),
    ("Volco un camion en la Ruta 40 a la altura de Albardon", "", None),
    ("Accidente en Caucete deja dos heridos", "", None),
    ("Motociclista herido tras siniestro vial en Chimbas", "", None),
]

ok = 0
fail = 0
for titulo, cuerpo, cat_esperada in tests:
    res = classify_article_with_python_rules(titulo, "", cuerpo)
    # Si cat_esperada es None, res debería ser None
    # Si cat_esperada es una categoría, res debería ser NO None (o coincidir en algo)
    correcto = (res is None) if (cat_esperada is None) else (res is not None)
    
    if correcto:
        ok += 1
        estado = "OK"
    else:
        fail += 1
        estado = "FALLA"
    
    accion = f"PASA ({res})" if res else "RECHAZA"
    print(f"[{estado}] {accion} | {titulo[:72]}")

print(f"\nResultado Clima: {ok}/{len(tests)} correctos, {fail} incorrectos")

if fail > 0:
    sys.exit(1)
else:
    sys.exit(0)
