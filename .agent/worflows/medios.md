# Configuración de Medios y Servicios - ZonData

Este documento detalla la configuración del motor de scraping híbrido (RSS + HTML), el flujo de pre-filtrado y la clasificación de incidentes.

---

## 1. Fuentes de Datos (Scraper Híbrido)

El sistema utiliza un agente de usuario (User-Agent) que simula un navegador real (Googlebot) para evitar bloqueos por parte de los medios.

| Medio | Método | URLs de Origen / Selectores | Estado |
| :--- | :--- | :--- | :--- |
| **Diario de Cuyo** | RSS | `policiales.xml`, `san-juan.xml` | Optimizada (Secciones) |
| **Tiempo de San Juan** | RSS | `Policiales.xml`, `home.xml` | Optimizada (Secciones) |
| **Diario Huarpe** | RSS | `policiales.xml`, `portada.xml` | Optimizada (Secciones) |
| **Canal 13 San Juan** | RSS | `/rss` | Completo |
| **Telesol Diario** | RSS | `/rss` | Completo |
| **Canal 4 San Juan** | RSS | `/feed/` | Completo |
| **Nuevo Mundo** | RSS | `/category/policiales/feed/` | Especializado |
| **Nuevo Diario** | RSS | `/feed` | Genérico |
| **La Provincia SJ** | RSS | `/rss` | Genérico |
| **San Juan 8** | RSS | `/rss` | Genérico |
| **Diario Móvil** | HTML | Raspado directo de artículos | HTML Directo |
| **0264Noticias** | HTML | Raspado directo de artículos | HTML Directo |

---

## 2. Ingesta, Pre-Filtrado y Cola SQLite

Para minimizar el consumo de recursos de red y costos de API, la ingesta opera en dos pasos:

### Paso 1: Escaneo y Pre-Filtrado de Titulares
* Se extrae el título y la descripción corta de la fuente (RSS o HTML selector).
* Se ejecuta localmente `classify_article_with_python_rules(title, description, None, rule)`:
  * **Si califica como posible incidente:** Se descarga el cuerpo del artículo (`fetch_article_text`), y se guarda en `raw_articles` con estado `'queued'`.
  * **Si no califica (policiales de robo, drogas, violencia familiar, política, deportes, etc.):** Se omite la descarga del cuerpo y se guarda directamente en `raw_articles` con estado `'ignored'`.
* Las siguientes corridas del scraper omitirán estas URLs de inmediato gracias a `is_url_processed()`.

### Paso 2: Procesamiento Diferido y Envío a API
* El script lee únicamente las noticias con estado `'queued'` en `raw_articles`.
* Se aplican las reglas estrictas de exclusión (armas de fuego, ruidos viales indirectos, retrospectivas).
* Si es un incidente verídico, se llama a Gemini (extracción de dirección, víctimas y vehículos) y a Google Maps (geolocalización).
* Si la API falla, se almacena como `'failed'` para reintentar. Si tiene éxito, se envía a Laravel y cambia a `'processed'`.

---

## 3. Recomendaciones y Sugerencias de Mejora

> [!TIP]
> **Detección de Falsos Positivos:** El sistema ya filtra palabras viales simuladas (ej: "simulacro", "taller de educación vial"). Se debe mantener la lista de `BLACKLIST_KEYWORDS` actualizada en `rss_scraper.py`.

> [!IMPORTANT]
> **Geocodificación Aproximada:** El flag `is_approximate` en el JSON transmitido a Laravel es vital. Si Gemini extrae una ubicación general (como un departamento general, ej: "Sarmiento"), se geocodifica como aproximado, informando al usuario en el mapa y previniendo colisiones de fusión indeseadas con otros reportes en la cabecera departamental.

> [!NOTE]
> **Escalabilidad de Cola:** El uso de SQLite para la cola `raw_articles` permite escalar el scraper de manera segura y desacoplada del servidor web de Laravel, posibilitando la ejecución de reintentos sin bloquear los hilos principales.
