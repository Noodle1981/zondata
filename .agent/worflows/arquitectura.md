# Arquitectura Técnica: ZonData

## Stack Tecnológico
- **Frontend:** React + Leaflet.js (Mapa interactivo) integrado en Laravel Blade.
- **Backend:** Laravel (PHP) como API y administrador de incidentes (Backpack).
- **Ingesta:** Scripts de Python (Scrapers) independientes en `/scrapers`.
- **Base de Datos:** SQLite (`database.sqlite`) para persistencia local de incidentes, configuraciones de fuentes y caché unificado de geocodificación.

## El Ciclo de Vida del Incidente
1. **Detección & Deduplicación:** Los scripts de Python revisan RSS y portadas de medios de San Juan (ej. SanJuan8, Telesol, Huarpe).
   - *Guardia de Hash*: Se calcula un MD5 del título y la fecha. Si ya fue procesado, se descarta.
   - *Guardia de Ruido*: Se filtran hechos delictivos/policiales (balaceras, robos armados).
2. **Geocodificación (Funnel de Precisión de 2 Niveles):**
   - **Nivel 1 (SQLite Cache):** Si la dirección de la calle y localidad exacta ya está en `geocoding_cache`, recupera las coordenadas instantáneamente (costo $0, latencia cero).
   - **Nivel 2 (Google Geocoding API):** Si es nueva, se geocodifica directamente mediante Google Maps API con restricciones estrictas de región (`region: ar`) y componentes (`administrative_area: San Juan | country: AR`) para garantizar precisión máxima. Se registra la precisión del tipo (`ROOFTOP`, `RANGE_INTERPOLATED`, `GEOMETRIC_CENTER`, `APPROXIMATE`) y el origen (`google`).
3. **Validación:** El sistema inyecta el evento en la API de Laravel (`/api/incidents`) con sus metadatos de precisión de geocodificación.
4. **Visualización:** React renderiza los eventos activos en el mapa provincial. Los incidentes muestran badges interactivos con el origen de sus coordenadas y el nivel de precisión técnica de Google.