<?php
require __DIR__ . '/../vendor/autoload.php';
$app = require_once __DIR__ . '/../bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

use App\Models\Incident;
use App\Http\Controllers\Api\IncidentController;
use Illuminate\Http\Request;

// 1. Clean previous test runs
Incident::where('description', 'like', '%Melani Desseff%')
    ->orWhere('title', 'like', '%Melani Desseff%')
    ->delete();

echo "Deleted old test data.\n";

$controller = new IncidentController();

// Simulate Report 1: Tiempo de San Juan (Wrong Location, Low Precision)
$request1 = Request::create('/api/incidents', 'POST', [
    'etiqueta' => 'Choque',
    'titulo' => '¿Quién es Melani Desseff Test? La estudiante de enfermería que quedó en terapia intensiva',
    'descripcion' => 'Con apenas 23 años, Melani Desseff Test atraviesa la pelea más difícil de su vida. La joven sanjuanina, estudiante de enfermería y mamá de una niña de 4 años, permanece internada en terapia intensiva tras protagonizar un violento choque en Rivadavia que la dejó gravemente herida. Fuentes vinculadas a la investigación indicaron que el hecho se produjo cerca de las 7:20 en la intersección de Avenida Ignacio de la Roza y calle Morón, en Rivadavia.',
    'latitud' => -31.5375, // approximate location in Rivadavia
    'longitud' => -68.5833,
    'is_approximate' => true,
    'source' => 'google',
    'location_type' => 'APPROXIMATE',
    'is_fatal' => false,
    'fuente_nombre' => 'Tiempo de San Juan',
    'fuente_url' => 'https://www.tiempodesanjuan.com/policiales/quien-es-melani-desseff-la-estudiante-enfermeria-que-quedo-terapia-intensiva-un-choque-n430926',
    'event_date' => '2026-05-22 07:20:00',
]);

echo "Sending Report 1 (Tiempo de San Juan)...\n";
$response1 = $controller->store($request1);
echo "Response 1 Status: " . $response1->getStatusCode() . "\n";
echo "Response 1 Content: " . $response1->getContent() . "\n\n";

// Simulate Report 2: Diario La Provincia SJ (Correct Location, High Precision, 3.9km away)
$request2 = Request::create('/api/incidents', 'POST', [
    'etiqueta' => 'Choque',
    'titulo' => 'Enfermera atropellada: un video y el test de alcoholemia, las claves de la investigación',
    'descripcion' => 'El hecho ocurrió pasadas las 7 de la mañana en la intersección de calles Comercio y Morón. La víctima, Melani Desseff Test, de 23 años, sufrió graves heridas y se encuentra internada en terapia intensiva en estado delicado.',
    'latitud' => -31.5437826, // high precision correct location (3.9km away from Report 1)
    'longitud' => -68.6245109,
    'is_approximate' => false,
    'source' => 'google',
    'location_type' => 'RANGE_INTERPOLATED',
    'is_fatal' => false,
    'fuente_nombre' => 'Diario La Provincia SJ',
    'fuente_url' => 'https://diariolaprovinciasj.com/policiales/enfermera-atropellada-un-video-y-el-test-de-alcoholemia-las-claves-de-la-investigacion-341179/',
    'event_date' => '2026-05-22 07:15:00',
]);

echo "Sending Report 2 (Diario La Provincia SJ)...\n";
$response2 = $controller->store($request2);
echo "Response 2 Status: " . $response2->getStatusCode() . "\n";
echo "Response 2 Content: " . $response2->getContent() . "\n\n";

// Verify the result in database
$incident = Incident::where('description', 'like', '%Melani Desseff%')->first();
if ($incident) {
    echo "=== VERIFICATION RESULT ===\n";
    echo "ID: " . $incident->id . "\n";
    echo "Title: " . $incident->title . "\n";
    echo "Victim Name(s): " . $incident->victim_names . "\n";
    echo "Latitude: " . $incident->latitude . " (Expected: -31.5437826)\n";
    echo "Longitude: " . $incident->longitude . " (Expected: -68.6245109)\n";
    echo "Location Type: " . $incident->location_type . " (Expected: RANGE_INTERPOLATED)\n";
    echo "Is Approximate: " . ($incident->is_approximate ? 'YES' : 'NO') . " (Expected: NO)\n";
    echo "Road Type: " . $incident->road_type . "\n";
    echo "Road Name: " . $incident->road_name . "\n";
    echo "Description enriched length: " . strlen($incident->description) . "\n";
    echo "============================\n";
} else {
    echo "ERROR: Incident not found in database!\n";
}
