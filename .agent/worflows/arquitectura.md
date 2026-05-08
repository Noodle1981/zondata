# Arquitectura Técnica: ZonData

## Stack Tecnológico
- **Frontend:** React + Leaflet.js (Mapa interactivo) integrado en Laravel Blade.
- **Backend:** Laravel (PHP) como API y administrador de incidentes (Backpack).
- **Ingesta:** Scripts de Python (Scrapers) independientes en `/scrapers`.
- **Base de Datos:** MySQL para persistencia de incidentes y logs de scraping.

## El Ciclo de Vida del Incidente
1. **Detección:** Los scripts de Python revisan RSS y portadas de medios de San Juan (ej. SanJuan8, Huarpe).
2. **Geocodificación:** Se procesa la dirección mencionada en la noticia para obtener Lat/Lng.
3. **Validación:** El sistema inyecta el evento en la API de Laravel con estado "Pendiente" o "Publicado".
4. **Visualización:** React renderiza los eventos activos en el mapa provincial mediante filtros laterales.