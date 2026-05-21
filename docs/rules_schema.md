# Esquema de Reglas del Scraper (`scraper_rules.json`)

El archivo `config/scraper_rules.json` y la tabla `scraper_rules` en la base de datos de SQLite controlan dinámicamente cómo el scraper de Zondata interactúa con los distintos medios de noticias, procesa los textos y los geocodifica.

## Estructura Principal
El JSON cuenta con dos raíces:
- `global`: Valores por defecto para cualquier dominio.
- `sources`: Diccionario donde las claves son el nombre del dominio (`diariomovil.info`).

## Campos por Dominio (Sources)

- **`type`** (string): Define si el scraper a utilizar es `"html"` o `"rss"`.
- **`scrape_urls`** (array de strings): Lista de URLs exactas a recorrer. Un medio puede tener varias secciones (e.g. policiales, portada).
- **`article_selector`** (string): (Sólo para `type: html`). Expresión regular que debe capturar 3 grupos:
  1. La URL relativa/absoluta del artículo.
  2. El título de la noticia.
  3. (Opcional) El copete o descripción de la noticia.
- **`sanitize_exclusions`** (array de strings): Frases o palabras que se deben eliminar del texto antes de pasarlo al buscador geográfico (e.g. `["Hospital Rawson"]` para evitar falsos positivos de ubicación en Capital/Rawson).
- **`ignore_terms`** (array de strings): Si el artículo contiene alguna de estas frases (case-insensitive), se descarta de forma inmediata. Útil para filtrar notas de publicidad o sorteos.
- **`priority`** (int): Orden de prioridad del scraper (default 1).
- **`custom_context`** (string): Se agrega al final de cada consulta a Nominatim si se conoce de antemano el área precisa (e.g. `"Rivadavia, San Juan"`). Si es `null`, se usan las jerarquías locales.
- **`hierarchy_overrides`** (objeto): Un mapeo `{"Nombre Localidad": "Nombre Departamento"}` para forzar la vinculación de una localidad cuando las tablas maestras de la DB causan conflicto.
- **`deep_fetch`** (bool): Indica si el scraper debe acceder a la URL y descargar el cuerpo entero de la noticia cuando no encuentra coordenadas exactas en el titular/descripción. Por defecto `true`.
- **`duplicate_check`** (bool): Evita descargar e interpretar repetidamente URLs que ya se encuentran guardadas en la base de datos de Zondata. Por defecto `true`.

## Flujo de Edición
1. Modifica `scraper_rules.json` y commitea tus cambios.
2. Si deseas actualizarlo en producción al instante, haz un UPDATE sobre la tabla `scraper_rules` de SQLite; la aplicación siempre da prioridad a lo guardado en la base de datos.
