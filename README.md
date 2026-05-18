<p align="center">
  <img src="public/images/logo.jpeg" width="300" alt="ZonData Logo" style="border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
</p>

# 📍 ZonData - Plataforma de Monitoreo de Incidentes en Tiempo Real

ZonData es una aplicación web interactiva diseñada para el monitoreo automatizado de incidentes críticos (meteorológicos, siniestros viales e incendios) en la Provincia de San Juan, Argentina. 

El sistema extrae noticias automáticamente mediante scrapers inteligentes en Python, geolocaliza los eventos en base a un análisis jerárquico de localidades y departamentos de la base de datos, y los visualiza en tiempo real en un mapa dinámico e interactivo.

---

## 🛠️ Stack Tecnológico

El proyecto está diseñado bajo una arquitectura desacoplada pero altamente sincronizada:

*   **Backend (API Rest):** Laravel 11 (PHP)
*   **Base de Datos:** SQLite (ligera, veloz y autocontenida)
*   **Frontend (Panel & Mapa):** React 19 + Leaflet Map + Tailwind CSS (Vite)
*   **Data Ingestion (Scrapers):** Python 3 + Geolocalización inteligente (`geopy` & `Nominatim` de OpenStreetMap)

---

## 📦 Requisitos Previos

Antes de comenzar la instalación en una nueva máquina, asegúrate de contar con los siguientes componentes en tu sistema:

1.  **PHP** >= 8.2 (junto con [Composer](https://getcomposer.org/))
2.  **Node.js** >= 18 (junto con `npm`)
3.  **Python** >= 3.10 (junto con `pip`)
4.  **Laravel Herd** o **Laragon** (Altamente recomendado para manejar dominios locales `.test` y PHP automáticamente)

---

## 🚀 Guía de Instalación y Puesta en Marcha

Sigue estos sencillos pasos para clonar y levantar el proyecto de forma local en pocos minutos:

### 1. Clonar el repositorio
```bash
git clone https://github.com/Noodle1981/zondata.git
cd zondata
```

### 2. Configurar las Variables de Entorno (`.env`)
Crea una copia del archivo de ejemplo para configurar tus credenciales locales:
```bash
cp .env.example .env
```
Abre el archivo `.env` recién creado y define la URL asignada por tu servidor de desarrollo. 
*   **Si usas Laravel Herd o Laragon (Recomendado):**
    ```env
    APP_URL=http://zondata.test
    DB_CONNECTION=sqlite
    ```
*   **Si utilizas el servidor local integrado de PHP (`artisan serve`):**
    ```env
    APP_URL=http://127.0.0.1:8000
    DB_CONNECTION=sqlite
    ```

### 3. Instalar Dependencias del Servidor e Iniciar Base de Datos
Instala las librerías necesarias de PHP:
```bash
composer install
```
Genera la clave de seguridad única de la aplicación:
```bash
php artisan key:generate
```
Crea y siembra la base de datos local SQLite (**este paso es fundamental** para inicializar las tablas de departamentos y localidades de San Juan que utiliza el geolocalizador):
```bash
php artisan migrate:fresh --seed
```

### 4. Instalar Dependencias del Frontend y de Python
Instala los paquetes de React y herramientas de compilación de assets:
```bash
npm install
```
Instala los módulos de Python necesarios para correr los scrapers:
```bash
pip install -r requirements.txt
```

---

## 💻 Ejecución del Proyecto

### Modo Integrado Completo (Recomendado)
El proyecto cuenta con un comando único que compila el frontend en tiempo real y ejecuta el scraper de noticias en segundo plano simultáneamente:
```bash
npm run start
```
*(Este comando levanta `Vite` y el daemon del scraper de Python en paralelo en la misma consola).*

### Servir el Backend Laravel (Opcional)
Si no utilizas Herd o Laragon, recuerda levantar tu servidor local de PHP en otra ventana de tu terminal para poder responder a las solicitudes de la API:
```bash
php artisan serve
```

### Ejecutar o Probar los Scrapers manualmente
*   **Ejecutar el Scraper en bucle constante (Modo Daemon):**
    ```bash
    npm run scraper
    ```
    *(Busca incidentes en los feeds locales de noticias cada 30 minutos de forma indefinida).*
*   **Ejecutar un escaneo único e inmediato:**
    ```bash
    python scrapers/rss_scraper.py
    ```
*   **Probar la ingesta manual de datos ficticios:**
    ```bash
    npm run test:sources
    ```

---

## 🤖 Automatización en Windows en Segundo Plano

Si estás en tu entorno de producción o desarrollo diario en Windows, puedes programar tareas del sistema para que el scraper de incidentes y el programador de tareas de Laravel se ejecuten automáticamente al iniciar sesión en el equipo de forma oculta:

1. Abre la terminal de **PowerShell como Administrador**.
2. Ejecuta el script automatizado de configuración:
   ```powershell
   ./setup_windows.ps1
   ```
3. El script registrará las tareas programadas correspondientes en tu sistema de manera permanente.

---

## 📁 Estructura Clave del Proyecto

*   `app/Http/Controllers/Api/IncidentController.php` — Controlador del backend que filtra, procesa y expone los incidentes publicados.
*   `database/seeders/LocationSeeder.php` — Semillas geográficas oficiales (Departamentos y Localidades de San Juan).
*   `scrapers/rss_scraper.py` — Algoritmo inteligente de ingesta, filtrado categórico por palabras clave y geolocalización jerárquica.
*   `resources/js/components/MapComponent.jsx` — Componente interactivo del mapa (Leaflet), filtros de incidentes y conteos premium.
