<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Incident;
use Illuminate\Http\Request;

class IncidentController extends Controller
{
    public function index(Request $request)
    {
        $query = Incident::with(['category', 'department', 'locality'])
            ->where('status', 'Published');

        $range = $request->query('range', 'today');
        $date  = $request->query('date'); // Fecha específica YYYY-MM-DD

        if ($date) {
            // Filtro por fecha específica
            $requestedDate = \Carbon\Carbon::parse($date);
            $daysAgo = now()->diffInDays($requestedDate, false);

            if ($daysAgo < -30) {
                // Más de 30 días: requiere suscripción Premium
                return response()->json([
                    'message' => 'Acceso Premium requerido para consultar datos históricos de más de 30 días.',
                    'upgrade_url' => '/premium'
                ], 402);
            }

            $query->whereDate('event_date', $requestedDate);
        } elseif ($range === 'today') {
            $query->whereDate('event_date', today());
        } elseif ($range === 'week') {
            $query->where('event_date', '>=', now()->subDays(7));
        } elseif ($range === 'month') {
            $query->where('event_date', '>=', now()->subDays(30));
        }

        $incidents = $query->orderBy('event_date', 'desc')->paginate(50);

        return response()->json($incidents);
    }

    private function normalizeText(string $text): string
    {
        $text = mb_strtolower($text, 'UTF-8');
        $replacements = [
            'á' => 'a', 'é' => 'e', 'í' => 'i', 'ó' => 'o', 'ú' => 'u',
            'ü' => 'u', 'ñ' => 'n'
        ];
        return strtr($text, $replacements);
    }

    private function resolveRoadInfo(string $title, ?string $description, float $latitude, float $longitude, ?int $localityId, ?int $departmentId): array
    {
        $roadType = 'Otro';
        $roadName = null;

        $textToSearch = $this->normalizeText($title . ' ' . ($description ?? ''));

        // 1. Detección de Circunvalación
        if (str_contains($textToSearch, 'circunvalacion')) {
            return [
                'road_type' => 'Circunvalación',
                'road_name' => 'Avenida de Circunvalación'
            ];
        }

        // 2. Detección de Ruta (Nacional o Provincial)
        if (preg_match('/(?:ruta\s+(?:nacional|provincial)?\s*|r\.?n\.?\s*|r\.?p\.?\s*)(\d+)/i', $textToSearch, $matches)) {
            $num = $matches[1];
            $isProv = str_contains($textToSearch, 'rp') || str_contains($textToSearch, 'provincial');
            $prefix = $isProv ? 'Ruta Provincial ' : 'Ruta Nacional ';
            return [
                'road_type' => 'Ruta',
                'road_name' => $prefix . $num
            ];
        }

        // 3. Detección de Calle o Avenida
        $streetPattern = '/(?:calle|avenida|av\.?|pasaje)\s+([a-z0-9áéíóúüñ\s]+?)(?=\s+(?:y|e|al|altura|en|frente|cerca|de)\b|$)/i';
        if (preg_match($streetPattern, $textToSearch, $matches)) {
            $nameCandidate = trim($matches[1]);
            if (strlen($nameCandidate) > 2 && strlen($nameCandidate) < 40) {
                $isAv = str_contains($textToSearch, 'avenida') || str_contains($textToSearch, 'av.');
                $prefix = $isAv ? 'Avenida ' : 'Calle ';
                $roadName = $prefix . ucwords($nameCandidate);
            }
        }

        // 4. Clasificación entre Urbana y Alejada
        $isGranSanJuan = false;
        if ($departmentId) {
            $dept = \App\Models\Department::find($departmentId);
            if ($dept) {
                $deptName = $this->normalizeText($dept->name);
                $urbanDepts = ['capital', 'rawson', 'rivadavia', 'chimbas', 'santa lucia'];
                if (in_array($deptName, $urbanDepts)) {
                    $isGranSanJuan = true;
                }
            }
        }

        if ($isGranSanJuan) {
            $roadType = 'Urbana';
        } else {
            $mentionsUrbanKeywords = false;
            foreach (['barrio', 'plaza', 'semaforo', 'esquina', 'microcentro', 'peatonal'] as $word) {
                if (str_contains($textToSearch, $word)) {
                    $mentionsUrbanKeywords = true;
                    break;
                }
            }

            $isLocalCenter = false;
            if ($localityId) {
                $loc = \App\Models\Locality::find($localityId);
                if ($loc) {
                    $locName = $this->normalizeText($loc->name);
                    if (str_contains($locName, 'caucete') || str_contains($locName, 'jachal') || str_contains($locName, 'villa krause') || str_contains($locName, 'san jose de jachal') || str_contains($locName, 'media agua')) {
                        $isLocalCenter = true;
                    }
                }
            }

            if ($mentionsUrbanKeywords || $isLocalCenter) {
                $roadType = 'Urbana';
            } else {
                $roadType = 'Alejada';
            }
        }

        return [
            'road_type' => $roadType,
            'road_name' => $roadName
        ];
    }

    private function resolveVehicleParticipation(string $title, ?string $description): array
    {
        $textToSearch = $this->normalizeText($title . ' ' . ($description ?? ''));

        $hasCar = false;
        $hasPickup = false;
        $hasUtility = false;
        $hasMotorcycle = false;
        $hasTruck = false;
        $hasBus = false;
        $hasPedestrian = false;
        $hasBicycle = false;

        // Autos
        foreach (['auto', 'automovil', 'vehiculo', 'remis', 'taxi'] as $word) {
            if (str_contains($textToSearch, $word)) {
                $hasCar = true;
                break;
            }
        }

        // Camionetas
        foreach (['camioneta', 'pickup', 'pick-up', 'hilux', 'amarok', 'ranger', 'suv'] as $word) {
            if (str_contains($textToSearch, $word)) {
                $hasPickup = true;
                break;
            }
        }

        // Utilitarios
        foreach (['utilitario', 'utilitarios', 'kangoo', 'berlingo', 'partner', 'fiorino', 'qubo', 'doblo', 'trafic', 'furgon'] as $word) {
            if (str_contains($textToSearch, $word)) {
                $hasUtility = true;
                break;
            }
        }

        // Motos
        foreach (['moto', 'motocicleta', 'motociclista', 'ciclomotor', 'motomel', 'zanella', 'honda wave'] as $word) {
            if (str_contains($textToSearch, $word)) {
                $hasMotorcycle = true;
                break;
            }
        }

        // Camiones
        foreach (['camion', 'semirremolque', 'acoplado', 'mosquito', 'chasis'] as $word) {
            if (str_contains($textToSearch, $word)) {
                $hasTruck = true;
                break;
            }
        }

        // Colectivos
        foreach (['colectivo', 'micro', 'omnibus', 'bus', 'redtulum', 'tulum'] as $word) {
            if (str_contains($textToSearch, $word)) {
                $hasBus = true;
                break;
            }
        }

        // Peatones
        foreach (['peaton', 'peatona', 'transeunte'] as $word) {
            if (str_contains($textToSearch, $word)) {
                $hasPedestrian = true;
                break;
            }
        }

        // Bicicletas
        foreach (['bici', 'bicicleta', 'ciclista'] as $word) {
            if (str_contains($textToSearch, $word)) {
                $hasBicycle = true;
                break;
            }
        }

        return [
            'has_car' => $hasCar,
            'has_pickup' => $hasPickup,
            'has_utility' => $hasUtility,
            'has_motorcycle' => $hasMotorcycle,
            'has_truck' => $hasTruck,
            'has_bus' => $hasBus,
            'has_pedestrian' => $hasPedestrian,
            'has_bicycle' => $hasBicycle
        ];
    }

    public function store(Request $request)
    {
        // Validación básica
        $validated = $request->validate([
            'etiqueta'     => 'required|string',
            'titulo'       => 'required|string|max:255',
            'descripcion'  => 'nullable|string',
            'latitud'      => 'required|numeric',
            'longitud'     => 'required|numeric',
            'is_approximate' => 'nullable|boolean',
            'is_fatal'     => 'nullable|boolean',
            'fuente_nombre' => 'nullable|string|max:255',
            'fuente_url'   => 'nullable|url',
            'verificado'   => 'nullable|boolean',
            'event_date'   => 'nullable|date',
        ]);

        // Buscar o crear la categoría según la etiqueta
        $category = \App\Models\Category::firstOrCreate(
            ['slug' => \Illuminate\Support\Str::slug($validated['etiqueta'])],
            ['name' => ucfirst($validated['etiqueta'])]
        );

        // Prevenir duplicados directos (Misma URL o Mismo Título)
        if (!empty($validated['fuente_url'])) {
            $existing = Incident::where('source_url', $validated['fuente_url'])->first();
            if ($existing) {
                return response()->json([
                    'message' => 'Incidente duplicado (URL ya registrada)',
                    'incident' => $existing
                ], 200);
            }
        }

        $existingTitle = Incident::where('title', $validated['titulo'])->first();
        if ($existingTitle) {
            return response()->json([
                'message' => 'Incidente duplicado (Título ya registrado)',
                'incident' => $existingTitle
            ], 200);
        }

        // --- Resolución de Jerarquía de Ubicaciones ---
        $localityId = null;
        $departmentId = null;
        $provinceId = null;

        $textToSearch = $this->normalizeText(($validated['titulo'] ?? '') . ' ' . ($validated['descripcion'] ?? ''));

        // Cargar todas las localidades con sus departamentos y provincias de forma optimizada
        $localities = \App\Models\Locality::with('department.province')->get();
        $departments = \App\Models\Department::with('province')->get();

        // Mapear cada localidad con su nombre principal "limpio" (coreName) para resolver distritos periféricos
        $localitiesWithCoreName = $localities->map(function ($locality) {
            $normalizedName = $this->normalizeText($locality->name);
            // Extraer parte antes de guión si existe (ej: "Vallecito - Paraje..." -> "Vallecito")
            $parts = explode('-', $normalizedName);
            $core = trim($parts[0]);
            // Quitar prefijos comunes
            $core = preg_replace('/^(bº|villa|paraje)\s+/', '', $core);
            $locality->core_name_cleaned = trim($core);
            return $locality;
        })->sortByDesc(function ($locality) {
            return strlen($locality->core_name_cleaned);
        });

        // 1. Buscar localidad en el texto (mayor especificidad)
        foreach ($localitiesWithCoreName as $locality) {
            $coreName = $locality->core_name_cleaned;
            if (strlen($coreName) > 3 && str_contains($textToSearch, $coreName)) {
                $localityId = $locality->id;
                $departmentId = $locality->department_id;
                if ($locality->department) {
                    $provinceId = $locality->department->province_id;
                }
                break;
            }
        }

        // 2. Si no se encontró localidad, buscar departamento
        if (!$localityId) {
            foreach ($departments as $department) {
                $normalizedDeptName = $this->normalizeText($department->name);
                if (strlen($normalizedDeptName) > 3 && str_contains($textToSearch, $normalizedDeptName)) {
                    $departmentId = $department->id;
                    $provinceId = $department->province_id;
                    break;
                }
            }
        }

        // 3. Fallback: Asociar por defecto a la provincia de San Juan
        if (!$provinceId) {
            $sjProvince = \App\Models\Province::where('name', 'San Juan')->first();
            if ($sjProvince) {
                $provinceId = $sjProvince->id;
            }
        }

        // --- Clasificación de Tipo de Vía y Nombre de Vía ---
        $roadInfo = $this->resolveRoadInfo(
            $validated['titulo'] ?? '',
            $validated['descripcion'] ?? '',
            (float) $validated['latitud'],
            (float) $validated['longitud'],
            $localityId,
            $departmentId
        );
        $roadType = $roadInfo['road_type'];
        $roadName = $roadInfo['road_name'];

        // --- Clasificación de Movilidades (Vehículos/Actores) ---
        $vehicles = $this->resolveVehicleParticipation(
            $validated['titulo'] ?? '',
            $validated['descripcion'] ?? ''
        );

        // --- Lógica de Asociación de Fallecimiento Post-Evento ---
        // Si el reporte actual es fatal, intentamos vincularlo a un accidente previo
        if (!empty($validated['is_fatal'])) {
            $isAccident = collect(['choque', 'vuelco', 'atropello', 'accidente', 'transito'])
                ->contains(fn($word) => str_contains(strtolower($validated['etiqueta']), $word));

            if ($isAccident) {
                // Buscamos un incidente en un radio de ~500m (0.005 grados) en los últimos 15 días
                // que sea de la misma zona pero que NO sea fatal todavía.
                $similarIncident = Incident::where('is_fatal', '!=', 1)
                    ->where('event_date', '>=', now()->subDays(15))
                    ->whereBetween('latitude', [$validated['latitud'] - 0.005, $validated['latitud'] + 0.005])
                    ->whereBetween('longitude', [$validated['longitud'] - 0.005, $validated['longitud'] + 0.005])
                    ->first();

                if ($similarIncident) {
                    $similarIncident->update([
                        'is_fatal' => true,
                        'description' => $similarIncident->description . "\n\n[ACTUALIZACIÓN FATAL]: " . $validated['titulo'] . " (Fuente: " . ($validated['fuente_url'] ?? 'N/A') . ")"
                    ]);

                    return response()->json([
                        'message' => 'Incidente previo actualizado a estado FATAL',
                        'incident' => $similarIncident
                    ], 200);
                }
            }
        }
        // ---------------------------------------------------------

        // --- Lógica de Duplicados Cercanos (Fuzzy) y Fusión Inteligente ---
        // Buscamos si ya hay un incidente de la misma categoría en un radio de ~1km
        // dentro de una ventana temporal de ±2 días (preservación cronológica).
        $eventDate = \Carbon\Carbon::parse($validated['event_date'] ?? now());
        $fuzzyDuplicate = Incident::where('category_id', $category->id)
            ->whereBetween('event_date', [
                $eventDate->copy()->subDays(2),
                $eventDate->copy()->addDays(2)
            ])
            ->whereBetween('latitude', [$validated['latitud'] - 0.01, $validated['latitud'] + 0.01])
            ->whereBetween('longitude', [$validated['longitud'] - 0.01, $validated['longitud'] + 0.01])
            ->first();

        if ($fuzzyDuplicate) {
            $existingHasLocality = !empty($fuzzyDuplicate->locality_id);
            $newHasLocality = !empty($localityId);
            
            $existingIsApprox = (bool) $fuzzyDuplicate->is_approximate;
            $newIsApprox = (bool) ($validated['is_approximate'] ?? false);

            $newLocationIsBetter = false;

            if ($existingIsApprox && !$newIsApprox) {
                // El nuevo es preciso y el existente era aproximado
                $newLocationIsBetter = true;
            } elseif (!$existingHasLocality && $newHasLocality) {
                // El nuevo tiene una localidad específica asociada y el existente no
                $newLocationIsBetter = true;
            }

            $updateData = [];

            if ($newLocationIsBetter || $fuzzyDuplicate->road_type === 'Otro' || empty($fuzzyDuplicate->road_name)) {
                $updateData['latitude'] = $validated['latitud'];
                $updateData['longitude'] = $validated['longitud'];
                $updateData['is_approximate'] = $newIsApprox;
                $updateData['locality_id'] = $localityId;
                $updateData['department_id'] = $departmentId;
                $updateData['province_id'] = $provinceId;
                $updateData['road_type'] = $roadType;
                $updateData['road_name'] = $roadName;
            }

            // Fusión aditiva de vehículos involucrados
            foreach (['has_car', 'has_pickup', 'has_utility', 'has_motorcycle', 'has_truck', 'has_bus', 'has_pedestrian', 'has_bicycle'] as $field) {
                if ($vehicles[$field] && !$fuzzyDuplicate->$field) {
                    $updateData[$field] = true;
                }
            }

            // Preservación Cronológica: Conservar la fecha más antigua (real del suceso)
            $existingEventDate = \Carbon\Carbon::parse($fuzzyDuplicate->event_date);
            if ($eventDate->lt($existingEventDate)) {
                $updateData['event_date'] = $eventDate;
            }

            // Si el nuevo es fatal y el existente no, actualizarlo
            if (($validated['is_fatal'] ?? false) && !$fuzzyDuplicate->is_fatal) {
                $updateData['is_fatal'] = true;
            }

            // Enriquecimiento de descripción: Concatenar detalles sin duplicar
            if (!empty($validated['descripcion'])) {
                $trimmedDesc = trim($validated['descripcion']);
                if (!str_contains($fuzzyDuplicate->description, $trimmedDesc)) {
                    $fuenteInfo = $validated['fuente_nombre'] ?? 'otra fuente';
                    $updateData['description'] = $fuzzyDuplicate->description . "\n\n[Reporte alternativo de " . $fuenteInfo . "]: " . $validated['descripcion'];
                }
            }

            if (!empty($updateData)) {
                $fuzzyDuplicate->update($updateData);
            }

            return response()->json([
                'message' => 'Incidente duplicado detectado. Se ha fusionado y enriquecido con la información actual.',
                'incident' => $fuzzyDuplicate
            ], 200);
        }
        // ---------------------------------------------

        $incident = Incident::create([
            'category_id'    => $category->id,
            'title'          => $validated['titulo'],
            'description'    => $validated['descripcion'],
            'source_name'    => $validated['fuente_nombre'] ?? 'ZonData Web',
            'source_url'     => $validated['fuente_url'] ?? 'http://zondata.test',
            'latitude'       => $validated['latitud'],
            'longitude'      => $validated['longitud'],
            'is_approximate' => $validated['is_approximate'] ?? false,
            'is_fatal'       => $validated['is_fatal'] ?? null,
            'status'         => 'Published',
            'event_date'     => $eventDate,
            'locality_id'    => $localityId,
            'department_id'  => $departmentId,
            'province_id'    => $provinceId,
            'road_type'      => $roadType,
            'road_name'      => $roadName,
            'has_car'        => $vehicles['has_car'],
            'has_pickup'     => $vehicles['has_pickup'],
            'has_utility'    => $vehicles['has_utility'],
            'has_motorcycle' => $vehicles['has_motorcycle'],
            'has_truck'      => $vehicles['has_truck'],
            'has_bus'        => $vehicles['has_bus'],
            'has_pedestrian' => $vehicles['has_pedestrian'],
            'has_bicycle'    => $vehicles['has_bicycle'],
        ]);

        return response()->json([
            'message' => 'Incidente registrado correctamente',
            'incident' => $incident
        ], 201);
    }
}
