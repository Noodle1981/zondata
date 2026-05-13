
# ZonData - Script de Configuracion Automatica de Windows
# Ejecutar UNA SOLA VEZ como Administrador
# Luego todo corre en background automaticamente

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ZonData - Configuracion de Automatizacion" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 1. Tarea: Laravel Scheduler (cada 1 minuto, para que el schedule:everyThirtyMinutes funcione)
Write-Host "[1/2] Registrando Laravel Scheduler en Windows Task Scheduler..." -ForegroundColor Yellow
schtasks /create `
    /tn "ZonData - Laravel Scheduler" `
    /tr "php D:\Zondata\artisan schedule:run" `
    /sc MINUTE `
    /mo 1 `
    /ru SYSTEM `
    /f | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK - Laravel Scheduler registrado (cada 1 minuto)" -ForegroundColor Green
} else {
    Write-Host "  ERROR - No se pudo registrar. Intenta ejecutar como Administrador." -ForegroundColor Red
}

# 2. Tarea: Python Scraper Daemon (al iniciar sesion en Windows)
Write-Host "[2/2] Registrando Python Scraper Daemon (al iniciar sesion)..." -ForegroundColor Yellow
schtasks /create `
    /tn "ZonData - Python Scraper Daemon" `
    /tr "python D:\Zondata\scrapers\rss_scraper.py --daemon" `
    /sc ONLOGON `
    /f | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK - Scraper Python registrado (inicia con Windows)" -ForegroundColor Green
} else {
    Write-Host "  ERROR - No se pudo registrar. Intenta ejecutar como Administrador." -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Configuracion completada!" -ForegroundColor Green
Write-Host ""
Write-Host "  - El scheduler de Laravel corre cada 30 min automaticamente."
Write-Host "  - El scraper Python arranca solo cuando inicias sesion en Windows."
Write-Host "  - No necesitas ejecutar nada mas."
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que las tareas quedaron registradas
Write-Host "Tareas registradas en el sistema:" -ForegroundColor Cyan
schtasks /query /tn "ZonData - Laravel Scheduler" /fo LIST 2>$null | Select-String "Nombre|Siguiente"
schtasks /query /tn "ZonData - Python Scraper Daemon" /fo LIST 2>$null | Select-String "Nombre|Siguiente"

Write-Host ""
Write-Host "Presiona cualquier tecla para cerrar..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
