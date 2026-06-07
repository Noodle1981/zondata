# Contexto del Proyecto: ZonData (Mapa de Incidentes)

## Visión
ZonData es una plataforma de monitoreo y análisis de eventos climáticos, de tránsito y siniestros en tiempo real para San Juan, Argentina. Centraliza incidentes reportados en la prensa y los expone estructuradamente en un mapa interactivo para facilitar la toma de decisiones ciudadana.

---

## Categorías de Eventos (Tags)
- **Viento:** Daños por viento Zonda o Sur, ramas y árboles caídos, postes o techos volados.
- **Tránsito:** Incidentes viales clasificados en Choques, Vuelcos y Atropellos.
- **Siniestros / Incendios:** Incendios de viviendas, pastizales/campos o vehículos.

---

## Reglas de Oro

1. **Atribución Obligatoria:** Cada pin en el mapa debe incluir el nombre y link al medio original (ej. "Fuente: Diario de Cuyo").
2. **Extracción Estructurada por IA:** El sistema utiliza Gemini para extraer metadatos limpios: Qué pasó, Dónde (Dirección para geocodificar), Quiénes (Nombres de víctimas) y Qué vehículos participaron.
3. **Consistencia Visual Naranja/Azul:** Naranja (#F28C28) para el "Zon" (fuego/viento/urgencia) y Azul Oscuro (#002D62) para el "Data" (seguridad/tecnología).
4. **Diseño de Popups Compactos (Sin Texto Plano):** Para mantener una interfaz limpia y libre de publicidad/ruido, los popups en el mapa no muestran la descripción en texto plano. En su lugar, utilizan badges/etiquetas visuales dinámicas para indicar los vehículos y la severidad del hecho.

---

## Calibración, Filtros y Deduplicación

5. **Pre-Filtrado de Titulares (Ahorro de APIs):** El sistema descarta noticias irrelevantes (policiales de robos/sangre, política, deportes, violencia familiar) analizando el título/descripción de forma local en Python antes de realizar el deep fetch (descarga del cuerpo), lo que reduce el consumo de red y APIs en un 90%.
6. **Guardia SQLite (`raw_articles`):** Todas las noticias procesadas se registran en una tabla intermedia con su estado correspondiente (`queued`, `processed`, `ignored`, `failed`) para evitar re-descargas.
7. **MD5 Content-Hash:** Se calcula a partir de `título + fecha_publicación` para omitir noticias duplicadas copiadas entre distintas agencias.
8. **Fusión Inteligente por Nombres Propios:** Si dos noticias coinciden en el nombre de una víctima (ventana de ±2 días), el backend en Laravel las fusiona automáticamente en un único incidente, acumulando vehículos de forma aditiva y adoptando la geolocalización de mayor nivel de precisión (`ROOFTOP` > `RANGE_INTERPOLATED` > `GEOMETRIC_CENTER` > `APPROXIMATE`).