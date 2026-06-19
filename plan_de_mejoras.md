# 🚀 Plan de Mejoras Integrales — ZonData

## Resumen Ejecutivo

ZonData es un sistema de mapa de incidentes en tiempo real para San Juan con un scraper híbrido RSS/HTML en Python, clasificación por reglas locales + Gemini AI (JSON Schema), geocodificación con Google Maps, y un frontend React+Leaflet sobre Laravel. La base es sólida. La revisión técnica exhaustiva encontró **15 problemas** (4 críticos, 7 importantes, 4 menores) y múltiples oportunidades de optimización.

---

## 🔴 Bugs Críticos Identificados (Prioridad Máxima)

> [!CAUTION]
> Estos 4 bugs afectan directamente la confiabilidad del sistema en producción y deben corregirse primero.

### Bug P1 — Gemini falla → todos los artículos quedan en `failed`
**Ubicación:** [`rss_scraper.py` L1211](file:///d:/Zondata/scrapers/rss_scraper.py)
```python
# Código actual: lanza Exception si Gemini no responde → raw_articles.status = 'failed'
if not gemini_res:
    raise Exception("No se pudo obtener respuesta válida de Gemini API...")
```
**Impacto:** Si la API de Gemini tiene downtime, TODOS los artículos en cola pasan a `failed` y nunca se reintentan automáticamente.  
**Fix:** En vez de lanzar excepción, marcar como `ignored` con mensaje descriptivo, o re-encolar con backoff.

### Bug P2 — Sin reintentos automáticos para artículos `failed`
`process_queued_articles()` solo lee `WHERE status = 'queued'`. Los artículos `failed` por timeout de Gemini o rate limit nunca se reintentan solos.  
**Fix:** Incluir artículos `failed` con más de 10 minutos de antigüedad en el query de reprocesamiento.

### Bug P3 — Conexiones SQLite abiertas y cerradas en cada operación
Se abre y cierra `sqlite3.connect(DB_PATH)` en cada función individualmente (`is_url_processed`, `save_raw_article`, `get_cached_coords`, etc.). Con 12 fuentes y 50+ artículos/ciclo → 100+ conexiones por ciclo.  
**Fix:** Pasar una conexión compartida a las funciones de acceso a DB dentro de cada ciclo principal, o usar un context manager global.

### Bug P4 — `classify_article_with_python_rules()` llamada DOS veces por artículo
Se llama en `scrape_rss()`/`scrape_html()` para decidir el deep fetch, y luego de nuevo en `analyze_news()` dentro de `process_queued_articles()`. El body_text ya está guardado en `raw_articles.body`.  
**Fix:** Guardar la categoría pre-clasificada como campo extra en `raw_articles` y leerla en el procesador.

### Bugs Importantes (P5–P15) Resumidos

| ID | Problema | Fix Rápido |
|----|----------|-----------|
| P5 | `ingest.py` es solo test hardcodeado, nombre engañoso | Renombrar a `test_ingest.py` |
| P6 | `scraper_rules.json` desactualizado vs SQLite real | Sincronizar o eliminar |
| P7 | `is_url_processed()`: 2 queries/artículo, podría pre-cargarse en un set | Set de URLs al inicio del ciclo |
| P8 | Fallback geocoding apunta siempre al centro de Capital → 10+ incidentes apilados | Usar coords del departamento detectado |
| P9 | Default `source='nominatim'` en geocoding_cache aunque Nominatim está descartado | Cambiar default a `'google'` |
| P10 | `resolveVehicleParticipation()` en Laravel redundante: Gemini ya envía todos los `has_*` | Eliminar lógica PHP de fallback |
| P11 | `extractProperNouns()` blacklist agresiva descarta nombres válidos de víctimas | Revisar blacklist |
| P12 | Polling frontend (30min) y daemon scraper (30min) no sincronizados | WebSockets o SSE |
| P13 | Estado `'Pending'` nunca usado por el scraper (envía directo `Published`) | Documentar o eliminar |
| P14 | Regex HTML scraping frágil para `diariomovil.info` | Migrar a BeautifulSoup |
| P15 | `raw_articles` nunca se purga, crece indefinidamente | Purga automática 7 días |

---

## 🕷️ 1. Pipeline de Scraping — Mejoras de Eficiencia

### 1.1 Pre-filtro Mejorado en la Fase de Ingesta
**Problema actual**: El scraper descarga el `body_text` completo (deep fetch) para TODOS los artículos que pasan el pre-filtro de título/descripción, antes de clasificarlos con Python. Esto genera muchas llamadas HTTP innecesarias.

**Mejora**: Aplicar la clasificación Python **antes** del deep fetch para los artículos con calidad de pre-filtro alta, y solo hacer deep fetch cuando la clasificación es dudosa o categoría ambigua.

```python
# Flujo mejorado propuesto:
# 1. Pre-filtro por título (ya existe) → descarta basura
# 2. Clasificación Python solo con título+descripción (score de confianza)
# 3a. Si score HIGH → deep fetch + Gemini (como ahora)
# 3b. Si score LOW → ignorar sin deep fetch
# 3c. Si score MEDIUM → deep fetch Python only, sin Gemini si ya clasifica bien
```

### 1.2 Tasa de Muestreo y Concurrencia
**Problema actual**: Los feeds se leen secuencialmente con `time.sleep(1)` entre artículos.

**Mejora**: Usar `concurrent.futures.ThreadPoolExecutor` para paralelizar el fetch de los distintos feeds RSS (no el procesamiento de artículos, que debe ser serial por los límites de API).

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(fetch_feed, url): url for url in all_feed_urls}
```

### 1.3 Limpieza Automática de `raw_articles`
**Problema actual**: Los artículos con estado `processed` e `ignored` se acumulan indefinidamente en la tabla `raw_articles`, aumentando el tamaño de la BD.

**Mejora**: Purga automática de artículos con más de 7 días y estado terminal (`processed`, `ignored`):

```python
def purge_old_raw_articles(days=7):
    """Elimina artículos terminales de más de N días para no inflar la DB."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM raw_articles 
        WHERE status IN ('processed', 'ignored')
        AND updated_at < datetime('now', '-? days')
    """, (days,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"[PURGE] {deleted} artículos eliminados de raw_articles.")
```

> [!IMPORTANT]
> Esta purga debe ejecutarse al inicio de cada ciclo del scraper para mantener la BD liviana.

### 1.4 Caché de Feeds RSS
**Problema actual**: Cada ejecución descarga el feed RSS completo sin importar si cambió.

**Mejora**: Respetar las cabeceras HTTP `ETag` y `Last-Modified` que los feeds de Diario Huarpe y otros ya envían, para evitar descargas redundantes:

```python
def fetch_feed_conditional(url, etag_cache):
    headers = {**get_headers(url)}
    cached = etag_cache.get(url)
    if cached:
        headers['If-None-Match'] = cached.get('etag', '')
        headers['If-Modified-Since'] = cached.get('last_modified', '')
    
    response = requests.get(url, headers=headers, timeout=15, verify=False)
    if response.status_code == 304:  # Not Modified
        return None  # Sin cambios, nada nuevo
    # ...actualizar cache de etag
    return response
```

---

## 🤖 2. Uso de Gemini AI — Optimización

### 2.1 Problema Actual
- Gemini se llama **para cada artículo** que pasa el pre-filtro, incluso cuando:
  - La clasificación Python ya fue muy precisa (categoría y subcategoría detectadas)
  - El artículo no tiene body text significativo
  - Ya tenemos la dirección de la descripción/título (no hace falta extraer)
- El límite de `MAX_GEMINI_CALLS_PER_RUN=30` es blando: los últimos artículos del ciclo se descartan si se alcanza.

### 2.2 Mejora: Estratificación de Llamadas a Gemini

Implementar niveles de confianza en la clasificación Python para determinar cuándo es necesario Gemini:

| Caso | Acción |
|------|--------|
| Python detecta categoría + dirección exacta (calle + altura) en título | Solo Gemini para `is_fatal`, `victim_names`, vehículos — **llamada ligera** |
| Python detecta categoría pero dirección ambigua | Gemini completo (como ahora) |
| Artículo pasa pre-filtro pero sin palabras de acción claras | Gemini como árbitro de `is_retrospective` solamente |

### 2.3 Prompt Mejorado para Gemini

El prompt actual es minimalista. Agregar contexto geográfico para reducir errores de ubicación:

```
Analiza la siguiente noticia de la provincia de San Juan, Argentina.
SAN JUAN es una provincia árida del oeste argentino, NO confundir con 
la ciudad de San Juan, Puerto Rico o Ciudad de San Juan en otros países.
Los departamentos de San Juan son: Capital, Rawson, Rivadavia, Chimbas...

Título: {title}
Descripción: {description}
Cuerpo: {body_text[:3000]}  ← Limitar body para no gastar tokens
```

### 2.4 Modo Batch para Gemini
Cuando hay múltiples artículos en cola, agrupar hasta 5 artículos en una sola llamada Gemini usando su API de batch o un prompt multi-artículo para reducir el costo en latencia y tokens.

### 2.5 Fallback Jerárquico para Extracción de Ubicación

Si Gemini devuelve `location_query` vago (solo departamento), intentar una segunda extracción más específica antes de aceptar la aproximación:

```python
# Si is_approximate=True y location_query es solo un departamento
# intentar extraer dirección del body_text con regex antes de aceptar
```

---

## 💻 3. LLM Local — Visión a Largo Plazo

### 3.1 Por qué tiene sentido un LLM local para ZonData

| Aspecto | Gemini API (actual) | LLM Local |
|---------|---------------------|-----------|
| Costo | Gratuito pero con límites | Costo de GPU, pero ilimitado |
| Latencia | ~1-3s por llamada | ~0.5-2s (GPU local) |
| Privacidad | Datos van a Google | Todo local |
| Fine-tuning | No posible | Muy posible con LoRA |
| Offline | No | Sí |

### 3.2 Modelos Recomendados (ordenados por utilidad para ZonData)

1. **`gemma-3-4b-it` (Google, cuantizado GGUF)** — El mejor balance. Mismo familia que Gemini, ideal para JSON estructurado, corre en 8GB RAM con CPU o 4GB VRAM GPU.

2. **`Llama-3.2-3B-Instruct-GGUF`** — Muy rápido, excelente en español con contexto específico. Funciona en CPU.

3. **`Qwen2.5-7B-Instruct`** — Mejor en español que Llama, excelente en extracción JSON estructurada, corre en GPU de 8GB.

### 3.3 Implementación Recomendada: `llama.cpp` + API local

```bash
# 1. Instalar llama.cpp con servidor HTTP
pip install llama-cpp-python[server]

# 2. Levantar el servidor local (compatible con OpenAI API)
python -m llama_cpp.server --model models/gemma-3-4b-it-Q4_K_M.gguf --n_gpu_layers 35

# 3. En rss_scraper.py, usar el mismo esquema JSON pero contra endpoint local:
url = "http://localhost:8080/v1/chat/completions"  # Compatible OpenAI
```

> [!NOTE]
> El response schema JSON estructurado (el punto fuerte actual de Gemini Flash) también es compatible con llama.cpp mediante `grammar` sampling o `json_schema` en Ollama 0.3+.

### 3.4 Estrategia Híbrida Recomendada

- **Corto plazo**: Gemini Flash 2.5 (gratis, muy bueno)
- **Mediano plazo**: Fine-tuning de Gemma-3-4B con ~200 ejemplos de noticias de San Juan procesadas → mucho más preciso en toponimia local
- **Largo plazo**: LLM local con Ollama para independencia total

### 3.5 Fine-Tuning con Datos Propios (de mayor impacto)

La tabla `raw_articles` + `incidents` ya contiene datos de entrenamiento. Exportar pares `(título+descripción+body) → (location_query, category, is_fatal)` procesados correctamente para crear un dataset de fine-tuning de ~500 ejemplos.

---

## 🗺️ 4. Mejoras del Mapa

### 4.1 Modo Satélite y Cambio de Capas de Mapa

**Problema actual**: Solo hay una capa de mapa (CartoDB Voyager). No hay modo satélite.

**Mejora**: Implementar un selector de capas de mapa con múltiples opciones:

#### Opciones de TileLayer a Agregar

| Capa | URL | Descripción |
|------|-----|-------------|
| CartoDB Voyager (actual) | `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/...` | Limpia y moderna |
| Satélite Esri | `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}` | Imágenes satelitales de alta calidad, sin API key |
| OSM Standard | `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png` | Referencia |
| CartoDB Dark | `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png` | Modo oscuro |

#### Componente de Selector de Capa

```jsx
// Agregar en MapComponent.jsx
const MAP_LAYERS = {
  street: {
    name: 'Mapa',
    icon: '🗺️',
    url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    attribution: '© CartoDB'
  },
  satellite: {
    name: 'Satélite',
    icon: '🛰️',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles © Esri'
  },
  dark: {
    name: 'Oscuro',
    icon: '🌙',
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '© CartoDB'
  }
};

const [activeLayer, setActiveLayer] = useState('street');
```

> [!IMPORTANT]
> Esri World Imagery es **gratuita sin API key** y tiene muy buena resolución en San Juan. Ideal para el modo satélite.

### 4.2 Etiquetas de Departamento sobre el Mapa

Agregar un GeoJSON con popups o tooltips estáticos que muestren el nombre del departamento sobre el mapa al hacer hover:

```jsx
<GeoJSON
    data={departmentsGeoJSON}
    onEachFeature={(feature, layer) => {
        layer.bindTooltip(feature.properties.nombre, {
            permanent: true,
            direction: 'center',
            className: 'dept-label-tooltip'
        });
    }}
/>
```

### 4.3 Clustering de Marcadores

Cuando hay muchos incidentes superpuestos (ej: zona Capital con 10+ choques), los marcadores se solapan. Usar `react-leaflet-cluster`:

```bash
npm install react-leaflet-cluster
```

```jsx
import MarkerClusterGroup from 'react-leaflet-cluster';

<MarkerClusterGroup chunkedLoading>
    {filteredIncidents.map(incident => <Marker key={...} />)}
</MarkerClusterGroup>
```

### 4.4 Heatmap de Incidentes

Agregar una capa de mapa de calor para visualizar zonas de alta concentración de incidentes (accidentes, incendios) usando `leaflet.heat`:

```bash
npm install leaflet.heat
```

### 4.5 Historial Temporal con Slider

Agregar un slider de tiempo en el pie del mapa para ver la evolución de incidentes a lo largo del día/semana.

---

## 🗃️ 5. Base de Datos — Limpieza y Eficiencia

### 5.1 Eliminar Acumulación en `raw_articles`

La tabla `raw_articles` actualmente guarda el `body` completo de TODAS las noticias clasificadas, incluso las que terminan siendo `ignored`. Esto acumula cientos de KB de texto por día innecesariamente.

**Mejora**: No guardar el body de artículos descartados, o limpiar el body tras clasificar:

```python
# En save_raw_article: no guardar body si ya se sabe que será ignorado
if potential_category is None:
    # No guardar body_text, reducir espacio
    body_text = None
```

### 5.2 Índices Faltantes

La tabla `incidents` ya tiene algunos índices, pero falta indexar el campo usado en el filtrado de duplicados:

```sql
CREATE INDEX IF NOT EXISTS idx_raw_articles_source_url ON raw_articles(source_url);
CREATE INDEX IF NOT EXISTS idx_raw_articles_status ON raw_articles(status);
CREATE INDEX IF NOT EXISTS idx_content_hash ON content_hash_cache(hash);
```

### 5.3 Expiración de `geocoding_cache`

Las coordenadas de calles no cambian, pero las intersecciones o lugares eventuales sí pueden variar. Agregar TTL de 30 días para entradas de baja precisión:

```sql
-- Limpiar entradas aproximadas de más de 30 días
DELETE FROM geocoding_cache 
WHERE is_approximate = 1 
AND created_at < datetime('now', '-30 days');
```

### 5.4 Compresión del Body en `raw_articles`

El campo `body` almacena hasta 10-15KB de HTML limpio por artículo. Comprimirlo con zlib reduce el tamaño ~70%:

```python
import zlib, base64

def compress_body(text):
    return base64.b64encode(zlib.compress(text.encode())).decode()

def decompress_body(compressed):
    return zlib.decompress(base64.b64decode(compressed)).decode()
```

---

## ✨ 6. Sugerencias Adicionales de Valor

### 6.1 Alertas en Tiempo Real con WebSocket

Para usuarios premium: un canal WebSocket que notifique en el momento en que se registra un nuevo incidente:

```php
// Laravel Broadcasting con Pusher o Reverb
event(new IncidentCreated($incident));
```

```jsx
// Frontend: suscripción a canal WebSocket
window.Echo.channel('incidents').listen('IncidentCreated', (e) => {
    // Agregar marcador al mapa sin recargar
    setIncidents(prev => [e.incident, ...prev]);
    showToastNotification(e.incident);
});
```

### 6.2 Detección de Patrones Repetidos

Si el mismo cruce o zona tuvo 3+ incidentes en 30 días, marcarlo como **punto negro** en el mapa con ícono diferenciado y estadística de peligrosidad. Útil para análisis de seguridad vial.

### 6.3 API Pública con Rate Limiting

Exponer un endpoint REST documentado (con Swagger/OpenAPI) para que organismos como Defensa Civil, CAPSJ o municipios puedan consumir los datos en tiempo real.

### 6.4 Imagen Previa de Noticia en el Popup

Extraer `og:image` del artículo fuente durante el deep fetch y mostrarla como miniatura en el popup del marcador del mapa para más contexto visual.

### 6.5 Panel de Monitoreo del Scraper

Una vista de admin en Laravel que muestre el estado en tiempo real de los artículos: cuántos `queued`, `processed`, `ignored`, `failed`, con su fecha y fuente. Actualmente esto solo se ve en la consola de Python.

### 6.6 Detección de Fuentes Nuevas / Caídas

Un job programado que valide periódicamente que todos los feeds RSS responden con `200 OK`. Si uno falla 3 veces consecutivas, enviar una notificación por email o Telegram al administrador.

### 6.7 Exportación de Datos Históricos

Permitir exportar los incidentes del mapa en formato CSV, GeoJSON o KMZ para uso en QGIS, Google Earth, o reportes municipales.

---

## 📋 Prioridades Recomendadas

| Prioridad | Mejora | Impacto | Esfuerzo |
|-----------|--------|---------|----------|
| 🔴 Alta | Modo satélite en el mapa (4.1) | Muy alto | Bajo (1-2hs) |
| 🔴 Alta | Purga de `raw_articles` (5.1, 1.3) | Alto | Bajo (1hs) |
| 🔴 Alta | Índices de BD faltantes (5.2) | Alto | Muy bajo (30min) |
| 🟡 Media | Cambio de capas / selector UI (4.1) | Alto | Medio (4hs) |
| 🟡 Media | Clustering de marcadores (4.3) | Alto | Bajo (2hs) |
| 🟡 Media | Estratificación Gemini (2.2) | Alto | Medio (4hs) |
| 🟡 Media | Concurrencia en fetch de feeds (1.2) | Medio | Bajo (2hs) |
| 🟡 Media | Etiquetas de departamentos (4.2) | Medio | Bajo (2hs) |
| 🟢 Baja | Prompt mejorado Gemini (2.3) | Medio | Muy bajo (30min) |
| 🟢 Baja | WebSockets / notificaciones (6.1) | Alto | Alto (2-3 días) |
| 🟢 Baja | LLM local con Ollama (3.3) | Alto | Alto (1 semana) |
| 🟢 Baja | Fine-tuning con datos propios (3.5) | Muy alto | Muy alto |

> [!TIP]
> Las primeras 3 mejoras (modo satélite, purga DB, índices) se pueden implementar hoy en menos de 3 horas con alto impacto visible inmediatamente.
