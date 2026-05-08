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