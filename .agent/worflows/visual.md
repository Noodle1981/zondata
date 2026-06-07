# Lineamientos Visuales e Identidad: ZonData

## 1. Paleta de Colores
Basándonos en la identidad del logo, definimos los códigos cromáticos principales:

*   **Naranja Zonda (#F28C28):** Representa el movimiento, el viento, el fuego y la alerta. Se usa para:
    *   La palabra "Zon" en el logotipo.
    *   Botones de acción principal (CTAs).
    *   Iconos y marcadores de incidentes climáticos y de urgencia (Vientos, Incendios).
*   **Azul Tecnológico (#002D62):** Representa los datos, la seguridad y la estabilidad. Se usa para:
    *   La palabra "Data" en el logotipo.
    *   Barras de navegación, cabeceras del panel lateral y pie de página.
    *   Tipografía principal y fondos oscuros.
*   **Colores de Alerta Secundarios:**
    *   **Rojo (#EF4444):** Únicamente para accidentes graves (con víctimas fatales) o alertas rojas críticas.
    *   **Ámbar (#F59E0B):** Para accidentes con lesionados o alertas amarillas preventivas.
    *   **Gris Claro (#F4F4F4):** Para fondos generales de secciones del mapa.

---

## 2. Tipografía
*   **Principal:** Sans-serif moderna (ej. Montserrat, Roboto o Instrument Sans) para facilitar la lectura rápida de datos en mapas.
*   **Estilo:** Bold/Black para etiquetas de eventos y nombres de departamentos; Regular/Medium para subtítulos y fechas.

---

## 3. Iconografía y Diseño del Mapa
*   **Estilo de Iconos:** Minimalistas y planos (Flat Design) con siluetas de vehículos, llamas o viento.
*   **Mapa Base:** Capa base de OpenStreetMap configurada en tonos claros/blancos (Voyager CartoDB) para que los pins resalten inmediatamente sin saturación visual.
*   **Pins de Mapa:** Marcadores circulares con el icono del evento en el centro. Borde azul para eventos generales, borde naranja/rojo para incidentes críticos.

---

## 4. Popups del Mapa (Badges / Sin Texto Plano)
Para asegurar que los popups mantengan una altura compacta y legible en pantallas móviles y de escritorio, **se prohíbe el renderizado de párrafos de texto plano de descripción**. En su lugar, el popup utiliza:
*   El **título** limpio de la noticia.
*   Una grilla de **badges de movilidad y severidad**:
    *   `💀 Fatal` (rojo) o `🩹 Lesionados` (ámbar).
    *   Iconos de vehículos: `🚗 Auto`, `🏍️ Moto`, `🛻 Camioneta`, `🚐 Utilitario`, `🚛 Camión`, `🚌 Colectivo`, `🚶 Peatón`, `🚲 Bicicleta`.
*   Una tarjeta interna estructurada en gris claro (`bg-gray-50`) para listar nombres de personas/víctimas si existen en la BD.

---

## 5. Directrices de Imágenes y Recursos
*   **Formato Estricto:** Las imágenes estáticas de la web deben utilizar el formato .jpg para optimizar la ligereza y velocidad de carga.
*   **Animaciones:** Se restringen a micro-animaciones (como el LED parpadeante de sincronización del panel lateral) para asegurar un rendimiento de 60fps en dispositivos móviles.