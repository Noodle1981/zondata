# Lineamientos Visuales e Identidad: ZonData

## 1. Paleta de Colores
Basándonos en la identidad del logo y en el enfoque exclusivo de incidentes climáticos, definimos los códigos cromáticos principales:

*   **Naranja Zonda (#F28C28):** Representa el viento, el fuego y las alertas meteorológicas. Se usa para:
    *   La palabra "Zon" en el logotipo.
    *   Botones de acción principal (CTAs).
    *   Iconos y marcadores de incidentes de viento Zonda, caída de ramas e incendios.
*   **Azul Tecnológico (#002D62):** Representa los datos, la seguridad y la estabilidad. Se usa para:
    *   La palabra "Data" en el logotipo.
    *   Barras de navegación, cabeceras del panel lateral y pie de página.
    *   Tipografía principal, fondos oscuros y marcadores de nieve, heladas o frío.
*   Colores de Alerta Secundarios (Por Categoría de Temporal en el Mapa):
    *   **Ramas / Viento** (`ramas`): Amarillo / Ámbar (`#EAB308` o `#F59E0B`).
    *   **Granizos** (`granizo`): Púrpura (`#8B5CF6`).
    *   **Inundaciones** (`inundacion`): Azul (`#3B82F6`).
    *   **Incendios** (`incendio`): Rojo (`#EF4444`).
    *   **Nieve** (`nieve`): Cian (`#06B6D4`).
    *   **Rayos** (`rayos`): Naranja (`#F97316`).
    *   **Círculo de Precisión Delineado:** Para incidentes con localización aproximada (`is_approximate = true`), se dibuja dinámicamente un círculo punteado concéntrico con el color correspondiente de la categoría (`stroke="${color}"`), lo que ayuda a identificar visualmente el nivel de certidumbre geográfica del reporte.

---

## 2. Tipografía
*   **Principal:** Sans-serif moderna (ej. Montserrat, Roboto o Instrument Sans) para facilitar la lectura rápida de datos en mapas.
*   **Estilo:** Bold/Black para etiquetas de eventos y nombres de departamentos; Regular/Medium para subtítulos y fechas.

---

## 3. Iconografía y Diseño del Mapa
*   **Estilo de Iconos:** Lucide Icons minimalistas y planos (Flat Design) encapsulados en pines circulares con colores específicos.
*   **Mapa Base:** Capa base de OpenStreetMap configurada en tonos claros/blancos (Voyager CartoDB) para que los pins resalten inmediatamente sin saturación visual.
*   **Pins de Mapa:** Marcadores circulares con el icono del evento en el centro. Borde azul para eventos generales, borde naranja/rojo para incidentes críticos.

---

## 4. Popups del Mapa (Badges / Sin Texto Plano)
Para asegurar que los popups mantengan una altura compacta y legible en pantallas móviles y de escritorio, **se prohíbe el renderizado de párrafos de texto plano de descripción**. En su lugar, el popup utiliza:
*   El **título** limpio de la noticia.
*   El **badge de la categoría climática** (`Ramas / Viento`, `Granizos`, `Inundaciones`, `Incendios`, `Nieve`, `Rayos`) con su color correspondiente.
*   Una tarjeta interna estructurada en gris claro (`bg-gray-50`) para mostrar información de la fuente (con enlace directo), fecha, origen de geocodificación y nivel de precisión.

---

## 5. Directrices de Imágenes y Recursos
*   **Formato Estricto:** Las imágenes estáticas de la web deben utilizar el formato .jpg para optimizar la ligereza y velocidad de carga.
*   **Animaciones:** Se restringen a micro-animaciones (como el LED parpadeante de sincronización del panel lateral) para asegurar un rendimiento de 60fps en dispositivos móviles.