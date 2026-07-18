<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use App\Models\Incident;
use App\Models\Category;
use Carbon\Carbon;

class TestCategoriesSeeder extends Seeder
{
    public function run(): void
    {
        // 1. Ramas / Viento (Amarillo)
        $catRamas = Category::firstOrCreate(['slug' => 'arboles-caidos'], ['name' => 'Arboles caidos']);
        Incident::firstOrCreate([
            'title' => 'Caída de ramas y cables cortados en Plaza 25 de Mayo por ráfagas de viento',
        ], [
            'category_id' => $catRamas->id,
            'description' => 'Las fuertes ráfagas de viento registradas en la tarde causaron la caída de varias ramas de gran tamaño y el corte de cables del tendido eléctrico público en los alrededores de la Plaza 25 de Mayo.',
            'source_name' => 'Diario de Cuyo',
            'source_url' => 'https://www.diariodecuyo.com.ar/san-juan/plaza-25-viento-n1',
            'latitude' => -31.5375,
            'longitude' => -68.5255,
            'event_date' => Carbon::parse('2026-07-18 15:30:00'),
            'status' => 'Published',
            'is_approximate' => false,
            'is_fatal' => false,
            'source' => 'google',
            'location_type' => 'ROOFTOP',
            'phenomenon_type' => 'zonda',
            'wind_cause' => true,
        ]);

        // 2. Granizo (Púrpura)
        $catGranizo = Category::firstOrCreate(['slug' => 'granizo'], ['name' => 'Granizo']);
        Incident::firstOrCreate([
            'title' => 'Fuerte granizada afectó cultivos vitivinícolas en la localidad de Media Agua',
        ], [
            'category_id' => $catGranizo->id,
            'description' => 'Una tormenta de granizo de gran intensidad azotó zonas productivas de Sarmiento, afectando hectáreas de viñedos y frutales. Vecinos reportaron piedras del tamaño de un huevo de gallina.',
            'source_name' => 'Tiempo de San Juan',
            'source_url' => 'https://www.tiempodesanjuan.com/sarmiento/granizo-n2',
            'latitude' => -32.1486,
            'longitude' => -68.5208,
            'event_date' => Carbon::parse('2026-07-18 16:15:00'),
            'status' => 'Published',
            'is_approximate' => true,
            'is_fatal' => false,
            'source' => 'google',
            'location_type' => 'GEOMETRIC_CENTER',
            'phenomenon_type' => 'tormenta',
            'wind_cause' => false,
        ]);

        // 3. Inundación (Azul)
        $catInundacion = Category::firstOrCreate(['slug' => 'inundacion-urbana'], ['name' => 'Inundacion urbana']);
        Incident::firstOrCreate([
            'title' => 'Desborde de canales e inundación de calzadas por intensas lluvias en Rivadavia',
        ], [
            'category_id' => $catInundacion->id,
            'description' => 'Las precipitaciones copiosas anegaron calles principales de la zona oeste del Gran San Juan, provocando el desborde de acequias y canales de riego con ingreso de agua en viviendas de bajo nivel.',
            'source_name' => 'Diario Huarpe',
            'source_url' => 'https://www.diariohuarpe.com/rivadavia/inundacion-n3',
            'latitude' => -31.5369,
            'longitude' => -68.5878,
            'event_date' => Carbon::parse('2026-07-18 17:00:00'),
            'status' => 'Published',
            'is_approximate' => false,
            'is_fatal' => false,
            'source' => 'google',
            'location_type' => 'RANGE_INTERPOLATED',
            'phenomenon_type' => 'tormenta',
            'wind_cause' => false,
        ]);

        // 4. Incendio (Rojo)
        $catIncendio = Category::firstOrCreate(['slug' => 'incendio-pastizales'], ['name' => 'Incendio pastizales']);
        Incident::firstOrCreate([
            'title' => 'Incendio de pastizales descontrolado movilizó a tres dotaciones de bomberos en Pocito',
        ], [
            'category_id' => $catIncendio->id,
            'description' => 'Un incendio de gran magnitud se desató en horas de la siesta sobre campos secos contiguos a la Ruta 40, amenazando viviendas cercanas debido al viento cambiante.',
            'source_name' => 'Diario 13 San Juan',
            'source_url' => 'https://www.canal13sanjuan.com/pocito/incendio-n4',
            'latitude' => -31.6583,
            'longitude' => -68.5822,
            'event_date' => Carbon::parse('2026-07-18 14:00:00'),
            'status' => 'Published',
            'is_approximate' => false,
            'is_fatal' => false,
            'source' => 'google',
            'location_type' => 'GEOMETRIC_CENTER',
            'phenomenon_type' => 'ninguno',
            'wind_cause' => false,
        ]);

        // 5. Nieve (Cian)
        $catNieve = Category::firstOrCreate(['slug' => 'nevada'], ['name' => 'Nevada']);
        Incident::firstOrCreate([
            'title' => 'Intenso temporal de nieve en la cordillera dejó incomunicado al Proyecto Los Azules',
        ], [
            'category_id' => $catNieve->id,
            'description' => 'Las precipitaciones níveas acumuladas superaron el metro y medio de altura en alta cordillera, obligando a las autoridades mineras a desmovilizar al personal de manera preventiva.',
            'source_name' => 'Diario de Cuyo',
            'source_url' => 'https://www.diariodecuyo.com.ar/san-juan/nieve-los-azules-n5',
            'latitude' => -31.1167,
            'longitude' => -70.2167,
            'event_date' => Carbon::parse('2026-07-18 10:00:00'),
            'status' => 'Published',
            'is_approximate' => true,
            'is_fatal' => false,
            'source' => 'google',
            'location_type' => 'APPROXIMATE',
            'phenomenon_type' => 'tormenta',
            'wind_cause' => false,
        ]);

        // 6. Rayos (Naranja)
        $catRayos = Category::firstOrCreate(['slug' => 'tormenta-electrica'], ['name' => 'Tormenta electrica']);
        Incident::firstOrCreate([
            'title' => 'Descarga eléctrica de un rayo afectó subestación transformadora en Chimbas',
        ], [
            'category_id' => $catRayos->id,
            'description' => 'Un fuerte rayo durante la tormenta eléctrica impactó de lleno sobre una subestación de energía, provocando un principio de incendio y dejando a medio departamento a oscuras.',
            'source_name' => 'Canal 4 San Juan',
            'source_url' => 'https://canal4sanjuan.com.ar/chimbas/rayo-n6',
            'latitude' => -31.4983,
            'longitude' => -68.5325,
            'event_date' => Carbon::parse('2026-07-18 18:20:00'),
            'status' => 'Published',
            'is_approximate' => false,
            'is_fatal' => false,
            'source' => 'google',
            'location_type' => 'GEOMETRIC_CENTER',
            'phenomenon_type' => 'tormenta',
            'wind_cause' => false,
        ]);
    }
}
