# Arquitectura Técnica: ZonData

## Stack Tecnológico
- **Frontend:** React + Leaflet.js (Mapa interactivo) integrado en Laravel Blade, compilado con Vite.
- **Backend:** Laravel (PHP) como API y administrador de incidentes (Backpack).
- **Ingesta:** Scripts de Python (Scrapers) independientes en `/scrapers` integrados con un sistema de cola SQLite local.
- **Base de Datos:** SQLite (`database.sqlite`) para persistencia local de incidentes, configuraciones de fuentes, caché unificado de geocodificación y la cola intermedia de ingesta.

---

## El Ciclo de Vida del Incidente

### 1. Ingesta y Pre-Filtrado (Python)
* **Pre-Filtrado Local por Titular:** Los scrapers escanean RSS y HTML de medios sanjuaninos. Antes de descargar el cuerpo del artículo (deep fetch), se evalúa el título y la descripción corta usando las reglas de exclusión y palabras clave de incidentes locales de Python.
* **Cola Desacoplada (`raw_articles`):** 
  * Si el artículo califica como un posible incidente, se realiza el deep fetch y se guarda en `raw_articles` con estado `'queued'`.
  * Si no califica (noticias de política, deportes o hechos de violencia familiar/delincuencia no viales), se descarta de inmediato y no se guarda en la base de datos, evitando la acumulación de datos innecesarios en la cola.
  * Si ocurre un error de API o timeout en fases subsiguientes, el estado se cambia a `'failed'` para reintentos posteriores.

### 2. Procesamiento Diferido (Python + APIs)
* El motor de procesamiento (`process_queued_articles`) lee los registros `'queued'` de `raw_articles`:
  * **Clasificación por Reglas de Python:** Se aplican las reglas estrictas de exclusión (armas de fuego, terminología de "giros", incidentes fuera de San Juan).
  * **Extracción Estructurada con Gemini:** Se envía el texto completo a Gemini 2.5 Flash para extraer:
    * `location_query`: Dirección exacta o paraje de referencia.
    * `is_fatal`: Severidad (fallecidos).
    * `victim_names`: Nombres propios completos de las víctimas involucradas.
    * Booleanos de participación de vehículos: `has_car`, `has_pickup`, `has_utility`, `has_motorcycle`, `has_truck`, `has_bus`, `has_pedestrian`, `has_bicycle`.
  * **Geocodificación de Alta Precisión:**
    * **SQLite Cache:** Busca coincidencias históricas en `geocoding_cache` (costo $0, latencia cero).
    * **Google Geocoding API:** Consulta con restricciones geográficas a San Juan, AR, registrando el `location_type` (`ROOFTOP`, `GEOMETRIC_CENTER`, etc.).

### 3. API y Fusión Inteligente de Duplicados (Laravel)
* Los datos estructurados se envían a `/api/incidents`.
* **Fusión por Nombres de Víctimas / Proximidad (±2 días, ~1.5 km):**
  * Si un nuevo reporte coincide temporalmente y es fatal, se asocia a accidentes previos usando los nombres propios extraídos por Gemini (o regex de fallback en PHP).
  * Si es duplicado, realiza una **fusión aditiva** de vehículos involucrados y consolida nombres (ej. actualizando "Melani" a "Melani Desseff").
  * **Precisión Dinámica:** El incidente adopta de manera automática las coordenadas y la dirección del reporte con mayor nivel de precisión de geocodificación (`ROOFTOP` > `RANGE_INTERPOLATED` > `GEOMETRIC_CENTER` > `APPROXIMATE`).

### 4. Visualización e Interfaz de Usuario (React)
* El mapa renderiza los incidentes mediante marcadores personalizados según la categoría.
* **Popup de Mapa Rediseñado (Badges / Sin Ruido):** Para evitar desbordamientos y publicidad de los diarios, se omiten las descripciones de texto plano en los popups. En su lugar, se renderiza una interfaz compacta que incluye:
  * El **título** limpio de la noticia.
  * Etiquetas de **severidad**: `💀 Fatal` (rojo) o `🩹 Lesionados` (ámbar).
  * Etiquetas de **vehículos involucrados**: Badges específicos con iconos (ej: `🚗 Auto`, `🏍️ Moto`).
  * Recuadro estructurado de **personas involucradas** (víctimas).
  * Datos de la fuente (con enlace directo), fecha, origen de geocodificación y nivel de precisión.