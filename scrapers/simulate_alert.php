<?php

// Incluir Laravel bootloader
require __DIR__ . '/../vendor/autoload.php';
$app = require_once __DIR__ . '/../bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

use App\Models\Incident;
use App\Models\AlertSubscriber;
use App\Jobs\SendClimateAlert;

echo "🧪 [SIMULACION] Iniciando prueba del sistema de alertas...\n";

// 1. Limpiar suscriptores de prueba anteriores
AlertSubscriber::where('email', 'test_alert@zondata.com')->delete();
AlertSubscriber::where('email', 'test_general@zondata.com')->delete();

// 2. Crear suscriptores de prueba
// Uno suscrito a 'zonda' en Ullum (id=14)
$sub1 = AlertSubscriber::create([
    'email' => 'test_alert@zondata.com',
    'phone' => '+549264555555',
    'department_id' => 14,
    'phenomenon_type' => 'zonda',
    'is_active' => true
]);

// Uno suscrito a todo en San Juan (id=null, phenomenon=null)
$sub2 = AlertSubscriber::create([
    'email' => 'test_general@zondata.com',
    'phone' => '+549264777777',
    'department_id' => null,
    'phenomenon_type' => null,
    'is_active' => true
]);

echo "✅ Suscriptores creados: \n";
echo "   - {$sub1->email} (Zonda en Ullum)\n";
echo "   - {$sub2->email} (General)\n";

// 3. Crear o simular un incidente
$incident = new Incident([
    'title' => 'Incendio forestal desatado por rafagas de Zonda en Ullum',
    'description' => 'Un incendio de grandes proporciones comenzo cerca de la Quebrada de Ullum por el viento Zonda.',
    'department_id' => 14,
    'phenomenon_type' => 'zonda',
    'source_name' => 'Diario de San Juan',
    'event_date' => now(),
]);

// Guardamos temporalmente para asociar relaciones en el log
$incident->id = 999; 

echo "\n📢 Disparando Job SendClimateAlert para el incidente:\n";
echo "   - Titulo: {$incident->title}\n";
echo "   - Departamento: Ullum (14)\n";
echo "   - Fenómeno: zonda\n";

// Ejecutamos el Job sincrónicamente para ver el resultado en caliente
$job = new SendClimateAlert($incident);
$job->handle();

echo "\n📊 Verificando logs generados:\n";
$logPath = storage_path('logs/alerts.log');
if (file_exists($logPath)) {
    echo "✅ Archivo alerts.log encontrado en storage/logs/alerts.log!\n";
    echo "--- Ultimas lineas del log ---\n";
    $lines = file($logPath);
    $lastLines = array_slice($lines, -5);
    foreach ($lastLines as $line) {
        echo "   " . trim($line) . "\n";
    }
    echo "------------------------------\n";
} else {
    echo "❌ No se encontro el archivo alerts.log en $logPath\n";
}

// Limpiar datos de prueba para no ensuciar la base de datos
$sub1->delete();
$sub2->delete();
echo "\n✨ Limpieza de prueba finalizada con exito.\n";
