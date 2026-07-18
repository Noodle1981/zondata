# Configuración de Medios y Servicios - ZonData

Este documento detalla la configuración del motor de scraping híbrido (RSS + HTML), el flujo de pre-filtrado y la clasificación de incidentes.

---

## 1. Fuentes de Datos (Scraper Híbrido)

El sistema utiliza un agente de usuario (User-Agent) que simula un navegador real estándar (Chrome) para evitar bloqueos por parte de los medios (especialmente Diario Huarpe, el cual bloquea bots como Googlebot con código de estado 403).

| Medio | Método | URLs de Origen / Selectores | Estado |
| :--- | :--- | :--- | :--- |
| **Diario de Cuyo** | HTML | Homepage y subpáginas con selector de artículos regex | Migrado a HTML (RSS congelado) |
| **Tiempo de San Juan** | RSS | `Policiales.xml`, `home.xml`, `san-juan.xml`, `mineria.xml` | Optimizada (Secciones) |
| **Diario Huarpe** | RSS | `policiales.xml`, `portada.xml`, `provinciales.xml` | Optimizada (Secciones) |
| **Canal 13 San Juan** | RSS | `/rss` | Completo |
| **Telesol Diario** | RSS | `/rss` | Completo |
| **Canal 4 San Juan** | RSS | `/feed/` | Completo |
| **Nuevo Mundo** | RSS | `/category/policiales/feed/`, `/category/locales/feed/` | Especializado |
| **Nuevo Diario** | RSS | `/feed` | Genérico |
| **La Provincia SJ** | RSS | `/rss` | Genérico |
| **San Juan 8** | RSS | `/rss` | Desactivado (404) |
| **Diario Móvil** | HTML | Raspado directo de artículos | HTML Directo |
| **0264Noticias** | HTML | Raspado directo de artículos (`/policiales`) | HTML Directo |

---

## 1.1 Monitoreo y Diagnóstico de Feeds (Panel de Control)

Con el fin de evitar feeds desactualizados o caídos (como ocurrió con el feed RSS de Diario de Cuyo), el sistema implementa una tabla de monitoreo en la base de datos principal (`scraper_sources`) conectada directamente al panel de administración en Laravel Backpack (`/admin/scraper-source`). 

El scraper actualiza dinámicamente los siguientes campos tras cada ejecución:
- `last_scraped_at` (datetime): Timestamp del último intento de lectura del medio.
- `last_article_at` (datetime): Timestamp del último artículo de incidente real guardado en la cola.
- `is_broken` (boolean): Bandera interna que marca si hubo un error de conexión, timeout o parseo.
- `error_message` (text): Detalle exacto del error devuelto por la petición HTTP.

### Alertas Visuales para el Admin:
- **⚠️ Roto (Rojo):** Se activa cuando `is_broken = 1`. Al pasar el cursor por encima del badge en el panel de control, se puede leer el mensaje de error exacto (ej: *HTTP 404*, *Timeout*).
- **⏳ Inactivo (Amarillo):** Se activa si la fuente está activa pero lleva más de 7 días sin capturar artículos nuevos (`last_article_at` antiguo), sugiriendo que el feed está congelado o requiere mantenimiento manual.
- **✅ Activo / OK (Verde):** La fuente responde exitosamente y tiene actividad reciente.

## 2. Ingesta, Pre-Filtrado y Cola SQLite

Para minimizar el consumo de recursos de red y costos de API, la ingesta opera en dos pasos:

### Paso 1: Escaneo y Pre-Filtrado de Titulares (Python Rules)
* Se extrae el título y la descripción corta de la fuente (RSS o HTML selector).
* Se ejecuta localmente `classify_article_with_python_rules(title, description, None, rule)`:
  * **Filtro de Predicciones y Alertas:** Si el artículo habla sobre alertas tempranas o pronósticos futuros (ej. "se espera viento Zonda", "se prevé granizo") y no reporta un hecho ya ocurrido, se descarta.
  * **Si califica como posible incidente confirmado:** Se descarga el cuerpo del artículo (`fetch_article_text`), y se guarda en `raw_articles` con estado `'queued'`.
  * **Si no califica:** Se omite la descarga del cuerpo por completo y la noticia no se almacena, previniendo el crecimiento excesivo de la base de datos.
* Se confirma explícitamente la transacción (`conn.commit()`) al finalizar la tanda de ingesta.

### Paso 2: Procesamiento Diferido y Envío a API
* El script lee únicamente las noticias con estado `'queued'` en `raw_articles`.
* Se aplican las reglas estrictas de exclusión (falsos incidentes viales, armas de fuego, retrospectivas).
* Si es un incidente verídico, se llama a Gemini (extracción de dirección, víctimas y vehículos) y a Google Maps (geolocalización).
* Si la API de Google falla, se activa el motor de geocoding de fallback local que prioriza localidades específicas (ej: Barreal, Rodeo) por encima de departamentos generales y evita el match de "Zonda" como lugar si corresponde al viento.
* Si el procesamiento tiene éxito, se envía a Laravel y cambia a `'processed'`.

---

## 3. Recomendaciones y Sugerencias de Mejora

> [!TIP]
> **Detección de Falsos Positivos:** El sistema ya filtra palabras viales simuladas (ej: "simulacro", "taller de educación vial") y de previsión del clima (ej: "se prevé", "pronostica"). Se debe mantener la lista de `PREDICTION_KEYWORDS` y `BLACKLIST_KEYWORDS` actualizada en `rss_scraper.py`.

> [!IMPORTANT]
> **Geocodificación Aproximada:** El flag `is_approximate` en el JSON transmitido a Laravel es vital. Si Gemini extrae una ubicación general (como un departamento general, ej: "Sarmiento"), se geocodifica como aproximado, informando al usuario en el mapa y previniendo colisiones de fusión indeseadas con otros reportes en la cabecera departamental.

> [!NOTE]
> **Escalabilidad de Cola:** El uso de SQLite para la cola `raw_articles` permite escalar el scraper de manera segura y desacoplada del servidor web de Laravel, posibilitando la ejecución de reintentos sin bloquear los hilos principales.
