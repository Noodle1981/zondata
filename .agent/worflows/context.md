# Contexto del Proyecto: ZonData (Inteligencia Climática Regional)

## Visión
ZonData es la primera plataforma de inteligencia climática geovinculada de San Juan, Argentina. Cruza incidentes reales (incendios, derrumbes, tormentas, nevadas, caídas de árboles) extraídos de medios locales con datos meteorológicos históricos en tiempo real (temperatura, ráfagas de viento, humedad, lluvias y anomalías ENSO) para identificar patrones, temporadas de riesgo y emitir alertas tempranas personalizadas.

---

## Enfoque Climático Exclusivo (Reenfoque 2026)
Para maximizar el valor de los datos y evitar redundancia:
- **Tránsito Puro Desactivado**: El scraping de accidentes viales comunes (choques rutinarios, infracciones) está completamente desactivado (`ENABLE_ACCIDENT_SCRAPING=false` en `.env`).
- **Accidentes Climáticos**: Solo se registran accidentes viales si fueron inducidos directamente por el clima (ej. hielo en calzada en cordillera, vuelco por ráfaga de viento, ruta anegada por crecidas).
- **Focos de Incendios**: Se capturan y analizan todos los incendios forestales, rurales y de pastizales, registrando estimaciones de hectáreas afectadas (`hectares_burned`), ya que son una consecuencia directa de la sequedad extrema y el viento Zonda.

---

## Categorías de Eventos y Fenómenos
El sistema clasifica e identifica de forma inteligente los siguientes fenómenos climáticos (`phenomenon_type`):
- **Zonda**: Viento cálido y seco que desata caídas de árboles, techos volados, cortes de energía e incendios forestales/pastizales.
- **Viento Sur**: Frente frío opuesto al Zonda, caracterizado por heladas, nevadas en cordillera y accidentes por congelamiento.
- **Tormentas**: Eventos estivales de lluvias torrenciales, granizo y descargas eléctricas.
- **Crecientes**: Crecidas de ríos o quebradas con arrastre de lodo e inundaciones urbanas o de pasos viales.
- **Derrumbes**: Desprendimientos de rocas y aludes en rutas nacionales/provinciales de montaña y corredores mineros (Ruta 40, Ruta 150).
- **Otro Climático**: Olas de calor extremo y sequía.

---

## Resolución de Conflicto Geográfico (El Departamento vs El Viento Zonda)
Para evitar que Gemini o el geocoder confundan el **viento Zonda** (fenómeno) con el **Departamento Zonda** (jurisdicción física):
1. El prompt de Gemini instruye explícitamente a diferenciar ambos conceptos según el contexto de la noticia.
2. Se procesan de forma independiente: un incidente puede localizarse en el *departamento de Ullum* pero estar catalogado con `phenomenon_type = 'zonda'` y tener `wind_cause = true`.
3. Si ocurre físicamente en el departamento Zonda, se geolocaliza allí mediante Nominatim de manera habitual.

---

## Enriquecimiento Meteorológico y ENSO (Fase 2)
Cada incidente procesado se enriquece automáticamente (`climate_enriched = true`):
1. **Open-Meteo Integration**: Se consulta retroactivamente el clima histórico para la fecha y coordenadas del incidente, extrayendo las métricas a la **hora pico de velocidad del viento** del día del evento (temperatura, ráfagas, humedad, dirección del viento y código WMO) y acumulando la precipitación diaria.
2. **Histórico ENSO (NOAA ONI)**: El sistema cuenta con una base de datos local de anomalías mensuales sembrada directamente desde NOAA (`enso_phases`), lo que permite clasificar instantáneamente si el incidente ocurrió durante la fase de **El Niño**, **La Niña** o fase **Neutro**.

---

## Sistema de Alertas y Monetización (Fase 5)
ZonData cuenta con un motor de suscripción y alertas tempranas:
- **Suscriptores**: Los usuarios (empresas mineras, transportistas, municipios) pueden registrarse especificando su correo electrónico, teléfono y opcionalmente filtrar por un departamento de interés o fenómeno climático específico.
- **Despacho**: Al ingresar un nuevo incidente clasificado, se despacha el Job `SendClimateAlert` en segundo plano, comparando filtros y generando alertas inmediatas que en desarrollo se escriben en `storage/logs/alerts.log`.