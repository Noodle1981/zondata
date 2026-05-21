import sys
sys.path.insert(0, 'd:/Zondata/scrapers')
from rss_scraper import analyze_news
from load_rules import load_rules, get_source_rule

rules = load_rules()
rule = get_source_rule(rules, 'tiempodesanjuan.com')

# Test 1: La noticia del museo de Lujan (Buenos Aires) - debe ser descartada
title1 = 'Temen que el incendio en un museo de Lujan haya reducido a cenizas parte de la historia sanjuanina'
desc1 = 'El incendio ocurrido en el Complejo Museografico Provincial Enrique Udaondo, en Lujan, Buenos Aires'
res1 = analyze_news(title1, desc1, 'https://test.com', 'Tiempo de San Juan', rule)
if res1 is None:
    print("Test Lujan-BsAs: DESCARTADA correctamente")
else:
    print("Test Lujan-BsAs: ERROR - fue aceptada cuando no debia")

# Test 2: Incendio en San Juan real - debe ser aceptada
title2 = 'Un incendio destruyo una vivienda en Capital, San Juan'
desc2 = 'El siniestro igneo ocurrio en la madrugada en Rawson. Los bomberos tardaron 2 horas.'
res2 = analyze_news(title2, desc2, 'https://test.com', 'Tiempo de San Juan', rule)
if res2 is not None:
    print("Test Incendio-SJ: ACEPTADA correctamente")
else:
    print("Test Incendio-SJ: Descartada - revisar")
