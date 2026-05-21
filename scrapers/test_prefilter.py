import sys
sys.path.insert(0, '.')
from rss_scraper import CONTEXT_WIND, CONTEXT_FIRE, CONTEXT_ACCIDENT, has_keyword_match

ALL_KW = CONTEXT_WIND + CONTEXT_FIRE + CONTEXT_ACCIDENT
print(f"Keywords viento   : {len(CONTEXT_WIND)}")
print(f"Keywords accidente: {len(CONTEXT_ACCIDENT)}")
print(f"Keywords incendio : {len(CONTEXT_FIRE)}")
print(f"Total pre-filtro  : {len(ALL_KW)}")
print()

tests = [
    # (titulo, deberia_pasar)
    ("Rivadavia ya comenzo a construir la segunda parada de colectivos", False),
    ("Dos sismos de Magnitud 3,5 sacudieron a San Juan", False),
    ("Politica y economia en San Juan: analisis del anio", False),
    ("Golpearon a una embarazada para robarle el celular", False),
    ("Inauguraron nuevo cuartel de bomberos en Rawson", False),
    ("Seguridad vial: charla en escuelas de Caucete", False),
    ("Estado del transito en Capital este lunes", False),
    # Deben pasar:
    ("Choque fatal en Rivadavia: murio el motociclista", True),
    ("Vuelco en Ruta 40: dos heridos graves", True),
    ("Incendio destruyo una vivienda en Chimbas", True),
    ("Atropello a un peatón y se dio a la fuga", True),
    ("Zonda: volo un techo y dejo sin luz a familias", True),
    ("Arbol caido interrumpio el transito en Avenida Libertador", True),
    ("Bomberos controlaron un incendio en pastizales de Pocito", True),
    ("Colision entre un auto y una moto en Capital", True),
    ("Se incendio una camioneta en plena Ruta 20", True),
    ("Volco un camion en la Ruta 40 a la altura de Albardon", True),
    ("Vientos fuertes causaron danos en varias zonas de San Juan", True),
    ("Rafagas de viento derribaron arboles en Caucete", True),
    ("Murio el conductor tras un choque multiple en Rawson", True),
    ("Accidente en Caucete deja dos heridos", True),
    ("Motociclista herido tras siniestro vial en Chimbas", True),
]

ok = 0
fail = 0
for titulo, esperado in tests:
    texto = titulo.lower()
    paso = any(has_keyword_match(texto, kw) for kw in ALL_KW)
    correcto = paso == esperado
    if correcto:
        ok += 1
        estado = "OK"
    else:
        fail += 1
        estado = "FALLA"
    accion = "PASA   " if paso else "RECHAZA"
    print(f"[{estado}] {accion} | {titulo[:72]}")

print(f"\nResultado: {ok}/{len(tests)} correctos, {fail} incorrectos")
