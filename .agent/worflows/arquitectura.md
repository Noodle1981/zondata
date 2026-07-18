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
* **Filtro de Alertas/Predicciones:** Se omiten aquellos artículos que solo reportan avisos meteorológicos a futuro o recomendaciones preventivas. Solo se capturan incidentes y fenómenos climáticos ya ocurridos.
* **Cola Desacoplada (`raw_articles`):** 
  * Si el artículo califica como un posible incidente, se realiza el deep fetch y se guarda en `raw_articles` con estado `'queued'`.
  * Si no califica (noticias viales comunes, política, deportes, robos, delincuencia, etc.), se descarta de inmediato, evitando la acumulación de datos innecesarios en la cola.

### 2. Procesamiento Diferido (Python + APIs)
* El motor de procesamiento (`process_queued_articles`) lee los registros `'queued'` de `raw_articles`:
  * **Clasificación por Reglas de Python:** Se aplican filtros de ruidos semánticos y exclusiones geográficas de fuera de la provincia.
  * **Extracción Estructurada con Gemini:** Se envía el texto completo a Gemini 2.5 Flash para extraer:
    * `location_query`: Dirección exacta, intersección o paraje de referencia.
    * `is_fatal`: Severidad (fallecidos).
    * `category`: Categoría climática de base de datos (ej. `arboles-caidos`, `granizo`, `inundacion-urbana`, `incendio-pastizales`, etc.).
    * `wind_cause`: Booleano que indica si el viento causó el incidente.
    * `phenomenon_type`: Tipo de fenómeno meteorológico (`zonda`, `viento_sur`, `tormenta`, `creciente`, `derrumbe`, `otro_climatico`).
  * **Geocodificación de Alta Precisión:**
    * **SQLite Cache:** Busca coincidencias históricas en `geocoding_cache` (costo $0, latencia cero).
    * **Google Geocoding API:** Consulta con restricciones geográficas a San Juan, AR, registrando el `location_type` (`ROOFTOP`, `GEOMETRIC_CENTER`, etc.).
    * **Fallback por Base de Datos:** Si falla Google, el sistema recurre a buscar departamentos o localidades en el texto mapeando a coordenadas de fallback fijas en memoria, priorizando la localidad por sobre el departamento.

### 3. API y Fusión Inteligente de Duplicados (Laravel)
* Los datos estructurados se envían a `/api/incidents`.
* **Fusión por Nombres de Víctimas / Proximidad (±2 días, ~1.5 km):**
  * Si un nuevo reporte coincide temporalmente y es fatal, se asocia a incidentes previos usando los nombres propios extraídos por Gemini.
  * Si es duplicado, realiza una **fusión aditiva** de datos y consolida información en el incidente principal.
  * **Precisión Dinámica:** El incidente adopta automáticamente las coordenadas y la dirección del reporte con mayor nivel de precisión de geocodificación (`ROOFTOP` > `RANGE_INTERPOLATED` > `GEOMETRIC_CENTER` > `APPROXIMATE`).

### 4. Visualización e Interfaz de Usuario (React)
* El mapa renderiza los incidentes mediante marcadores personalizados según las 6 categorías principales: **Ramas/Viento**, **Granizos**, **Inundaciones**, **Incendios**, **Nieve**, **Rayos**.
* **Popup de Mapa Rediseñado (Sin Ruido):** Para evitar desbordamientos, se omiten las descripciones de texto plano. En su lugar, se renderiza una interfaz compacta que incluye:
  * El **título** limpio de la noticia.
  * La **categoría de temporal** asociada con su color distintivo.
  * Etiquetas de **severidad**: `💀 Fatal` (rojo) o `🩹 Lesionados` (ámbar) si aplica.
  * Datos de la fuente (con enlace directo), fecha, origen de geocodificación y nivel de precisión.