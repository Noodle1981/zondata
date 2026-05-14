# Configuración de Medios y Servicios - ZonData

Este documento detalla la configuración del motor de scraping híbrido (RSS + HTML) y la lógica de clasificación de incidentes.

## 1. Fuentes de Datos (Scraper Híbrido)

El sistema utiliza un agente de usuario (User-Agent) que simula un navegador real para evitar bloqueos por parte de los medios.

| Medio | Método | URLs de Origen | Estado |
| :--- | :--- | :--- | :--- |
| **Diario de Cuyo** | RSS | `policiales.xml`, `san-juan.xml` | Optimizada (Secciones) |
| **Tiempo de San Juan** | RSS | `Policiales.xml`, `home.xml` | Optimizada (Secciones) |
| **Diario Huarpe** | RSS | `policiales.xml`, `portada.xml` | Optimizada (Secciones) |
| **Canal 13 San Juan** | RSS | `https://www.canal13sanjuan.com/rss` | Completo |
| **Telesol Diario** | RSS | `https://www.telesoldiario.com/rss` | Completo |
| **Canal 4 San Juan** | RSS | `https://canal4sanjuan.com.ar/feed/` | Completo |
| **Nuevo Mundo** | RSS | `category/policiales/feed/` | Especializado |
| **La Provincia SJ** | RSS | `https://www.diariolaprovinciasj.com/rss` | Genérico |
| **San Juan 8** | RSS | `https://www.sanjuan8.com/rss` | Genérico |
| **Diario Móvil** | HTML | `/categoria/4/san-juan` | Scraping Directo |
| **0264Noticias** | HTML | `/policiales` | Scraping Directo |

## 2. Clasificación de Servicios (Keywords)

El scraper clasifica automáticamente las noticias basándose en "Mapeos" de palabras clave.

### A. Servicio de Vientos (Prioridad 1)
*   **Contexto:** Detecta fenómenos climáticos que generan peligros en la vía pública.
*   **Keywords:** `viento`, `zonda`, `ráfaga`, `temporal`, `sudeste`, `alerta climática`.
*   **Categorías Resultantes:** Viento Zonda, Viento Sur, Alerta Meteorológica.

### B. Servicio de Accidentes Viales (Prioridad 2)
*   **Contexto:** Detecta siniestros de tránsito.
*   **Keywords por Sub-tipo:**
    *   **Choque:** `choque`, `colisión`, `impacto`, `chocó`, `siniestro`, `accidente`, `vial`.
    *   **Vuelco:** `vuelco`, `volcó`, `despistó`, `cayó`, `caída`, `caida`.
    *   **Atropello/Moto:** `atropelló`, `embistió`, `peatón`, `arrolló`, `moto`, `motociclista`.

### C. Servicio de Incendios (Prioridad 3)
*   **Contexto:** Detecta incendios en estructuras o vegetación.
*   **Keywords:** `fuego`, `incendio`, `llamas`, `bomberos`, `quemó`, `siniestro ígneo`.

## 3. Recomendaciones y Sugerencias de Mejora

> [!TIP]
> **Detección de Falsos Positivos:** Algunos accidentes son reportados como "Simulacros". Se recomienda agregar una "Lista Negra" de palabras como `simulacro`, `prevención` o `charla` para ignorar esas noticias.

> [!IMPORTANT]
> **Geocodificación Aproximada:** Cuando la noticia no menciona una calle exacta sino un barrio o zona (ej: "Barrio Rivadavia"), el sistema ubica el punto en el centro de ese barrio. Es vital mantener el flag `is_approximate` activo para informar al usuario que la ubicación no es exacta.

> [!NOTE]
> **Escalabilidad:** Si el número de fuentes HTML crece, se recomienda migrar el scraper a una base de datos de selectores (JSON o DB) para no tener los regex hardcodeados en el script de Python.
