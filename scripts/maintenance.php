<?php

require __DIR__.'/../vendor/autoload.php';
$app = require_once __DIR__.'/../bootstrap/app.php';

use App\Models\Incident;
use Illuminate\Support\Str;

$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

echo "--- Iniciando Mantenimiento de ZonData ---\n";

// 1. Actualizar decesos (Calaveras)
$fatalKeywords = ['murió', 'falleció', 'deceso', 'tragedia', 'muerto', 'sin vida', 'víctima fatal', 'occiso'];
$updatedFatal = 0;

Incident::whereNull('is_fatal')->get()->each(function($i) use ($fatalKeywords, &$updatedFatal) {
    $text = Str::lower($i->title . ' ' . $i->description);
    if (Str::contains($text, $fatalKeywords)) {
        $i->update(['is_fatal' => true]);
        $updatedFatal++;
        echo "[FATAL] Actualizado: {$i->title}\n";
    }
});

echo "\nTotal de decesos actualizados: $updatedFatal\n";

// 2. Limpieza de Categorías (Asegurar slugs correctos)
echo "Revisando categorías...\n";
Incident::all()->each(function($i) {
    $slug = $i->category->slug;
    // Si detectamos inconsistencias de nombres, aquí se pueden corregir
});

echo "--- Mantenimiento Finalizado ---\n";
