# Contexto del Proyecto: ZonData (Mapa de Incidentes)

## Visión
ZonData es una plataforma de monitoreo de eventos y contingencias en tiempo real para San Juan, Argentina. Centraliza incidentes dispersos en medios de comunicación en un mapa interactivo único para facilitar la toma de decisiones ciudadana.

## Categorías de Eventos (Tags)
- **Clima:** Vientos (Zonda/Sur), granizo, inundaciones por crecientes.
- **Servicios:** Cortes de luz programados o accidentales, falta de agua.
- **Tránsito:** Accidentes viales, calles cortadas por árboles caídos o protestas.
- **Siniestros:** Incendios y emergencias detectadas por la prensa.

## Reglas de Oro
1. **Atribución Obligatoria:** Cada pin en el mapa debe incluir el nombre y link al medio original (ej. "Fuente: Diario de Cuyo").
2. **Extracción de Metadatos:** El sistema no copia notas; extrae: Qué pasó, Dónde (Coordenadas) y Cuándo.
3. **Estética:** Naranja (#F28C28) para el "Zon" (fuego/viento) y Azul Oscuro (#002D62) para el "Data" (tecnología). 
4. **Simplicidad Visual:** Uso de iconos claros y mapas livianos (OpenStreetMap). Formato .jpg para cualquier recurso visual estático.

## Calibración y Filtros de Ruido (Nuevos Sistemas)
5. **Guardia Policial / Anti-Crímenes:** Para mantener el mapa libre de ruidos irrelevantes, las noticias policiales de sangre o robos violentos (delitos armados, balaceras con tiros/disparos, apuñalamientos) son **descartadas automáticamente** de las categorías de Incidentes e Incendios, a menos que involucren un siniestro vial o choque vehicular explícito.
6. **MD5 Content-Hash Dedup:** Evita el procesamiento redundante de geocodificación. Antes del geocoding, se calcula un hash MD5 a partir de `título + fecha_publicación`. Si otra URL publica la misma noticia clonada de una agencia, el sistema la detecta y descarta inmediatamente sin hacer llamadas a APIs de red.
7. **Detección de Víctimas y Auto-Corrección por Nombres Propios:** Para solucionar discrepancias y errores periodísticos de localización, el sistema extrae nombres propios de personas involucradas (ej. "Melani Desseff") tras limpiar referencias a calles y avenidas. Si dos reportes coinciden en el nombre propio en una ventana de ±2 días, se fusionan automáticamente y se promueve la geolocalización hacia el reporte con mayor precisión (ej. `ROOFTOP` o `RANGE_INTERPOLATED` sobre `APPROXIMATE`).