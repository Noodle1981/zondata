Etapa 6: Geolocalización Inteligente (Estrategia de Embudos)
Este plan define cómo transformaremos el texto de las noticias locales de San Juan en coordenadas precisas (Latitud y Longitud) para el mapa, solucionando el problema de la falta de direcciones exactas.

Arquitectura Propuesta: "El Embudo de Geolocalización"
Para optimizar costos y maximizar la precisión, el scraper implementará un sistema de validación en cascada. Si falla un nivel, pasa al siguiente:

Nivel 1: Búsqueda Directa y Exacta (Geopy)
Lógica: Extraer nombres de calles mediante expresiones regulares (ej. "calle X e intersección Y", "Avenida Z").
Acción: Enviar la cadena "Calle X y Calle Y, San Juan, Argentina" a la API gratuita de OpenStreetMap (Nominatim) a través de la librería geopy.
Resultado esperado: Coordenadas exactas del cruce. Si falla, pasa al Nivel 2.
Nivel 2: Validación Cruzada entre Medios
Lógica: Agrupar noticias similares (si Diario de Cuyo, Tiempo SJ y Diario Móvil reportan un choque a la misma hora).
Acción: Si una noticia dice "choque en capital" pero otra dice "choque en Libertador y Mendoza", el sistema unifica el incidente y toma las coordenadas precisas del segundo medio. Si ninguno tiene calle, pasa al Nivel 3.
Nivel 3: Aproximación Zonal (Punto Medio)
Lógica: El periodista solo reportó la zona general (ej. "Cayó un árbol en el Barrio Foeva" o "Siniestro en Chimbas").
Acción: Solicitar a Nominatim las coordenadas del centro geométrico del Barrio o Municipio mencionado.
Resultado: El pin se coloca en el medio de la zona, agregando una advertencia visual (ej. un borde gris en el mapa) que indica "Ubicación Aproximada". Si no menciona ni barrio ni calle, pasa al Nivel 4.
Nivel 4: Último Recurso (Kilómetro 0)
Lógica: La noticia es extremadamente genérica ("Hubo un accidente fatal en la provincia").
Acción: Colocar el pin en la Plaza 25 de Mayo (Km 0 de San Juan) pero con la tarjeta de información marcada como "Ubicación sin especificar".
Nivel 5: Comodín de Inteligencia Artificial (Opcional a Futuro)
Usar la API de Gemini para textos muy complejos donde la dirección está escrita de forma inusual, usándola únicamente como último recurso procesal para evitar costos innecesarios en la nube.
Próximos pasos para la siguiente sesión
Instalar geopy en el entorno virtual.
Escribir las funciones de extracción de texto (NLP Básico) en el rss_scraper.py.
Ajustar el backend para recibir un nuevo parámetro booleano is_approximate_location para que el mapa renderice los pines genéricos de forma diferente.