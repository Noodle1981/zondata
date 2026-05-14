<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>ZonData - Mapa de Incidentes en Tiempo Real</title>
        <meta name="description" content="ZonData: Monitoreo en tiempo real de incidentes viales, incendios y eventos climáticos en San Juan, Argentina. Mantente informado y seguro con nuestro mapa interactivo.">
        <meta name="keywords" content="incidencias, san juan, zonda, transito, accidentes, incendios, mapa en vivo, alertas climáticas">
        <meta name="author" content="ZonData">
        @viteReactRefresh
        @vite(['resources/css/app.css', 'resources/js/app.jsx'])
    </head>
    <body class="antialiased">
        <div id="map-root"></div>
    </body>
</html>
