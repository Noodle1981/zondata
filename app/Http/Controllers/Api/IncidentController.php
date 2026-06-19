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

    public function getSummary(Request $request)
    {
        $todayIncidents = Incident::whereDate('event_date', today())->get();
        $yesterdayIncidents = Incident::whereDate('event_date', today()->subDay())->get();

        return response()->json([
            'today' => [
                'count' => $todayIncidents->count(),
                'fatal' => $todayIncidents->where('is_fatal', true)->count(),
            ],
            'yesterday' => [
                'count' => $yesterdayIncidents->count(),
                'fatal' => $yesterdayIncidents->where('is_fatal', true)->count(),
            ]
        ]);
    }

    public function getNotifications(Request $request)
    {
        $notifications = \Illuminate\Support\Facades\DB::table('incident_notifications')
            ->join('incidents', 'incident_notifications.incident_id', '=', 'incidents.id')
            ->select('incident_notifications.*', 'incidents.title', 'incidents.source_url', 'incidents.source_name')
            ->whereDate('incident_notifications.created_at', today())
            ->orderBy('incident_notifications.created_at', 'desc')
            ->get();

        return response()->json($notifications);
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

        // 3. Detección de Calle o Avenida (y posibles intersecciones)
        // Intentar detectar primero una intersección: "Calle X y Calle Y"
        $intersectionPattern = '/(?:calle|avenida|av\.?|pasaje)?\s*([a-z0-9áéíóúüñ\s]+?)\s+(?:y|e|intersección\s+(?:de|con)?|cruce\s+(?:de|con)?|esquina)\s+(?:calle|avenida|av\.?|pasaje)?\s*([a-z0-9áéíóúüñ\s]+?)(?=\s+(?:al|altura|en|frente|cerca|de\s+la\b|\.|,|$))/i';
        
        if (preg_match($intersectionPattern, $textToSearch, $matches)) {
            $name1 = trim($matches[1]);
            $name2 = trim($matches[2]);
            if (strlen($name1) > 2 && strlen($name2) > 2) {
                // Limpiar conectores finales capturados por accidente
                $name1 = preg_replace('/\s+(de|del|la|las|los|el)$/i', '', $name1);
                $name2 = preg_replace('/\s+(de|del|la|las|los|el)$/i', '', $name2);
                $roadName = ucwords(trim($name1)) . ' y ' . ucwords(trim($name2));
            }
        }
        
        // Si no se encontró intersección, buscar calle simple
        if (!$roadName) {
            $streetPattern = '/(?:calle|avenida|av\.?|pasaje)\s+([a-z0-9áéíóúüñ\s]+?)(?=\s+(?:y|e|al|altura|en|frente|cerca|de\s+la\b|\.|,|$))/i';
            if (preg_match($streetPattern, $textToSearch, $matches)) {
                $nameCandidate = trim($matches[1]);
                if (strlen($nameCandidate) > 2 && strlen($nameCandidate) < 40) {
                    $isAv = str_contains($textToSearch, 'avenida') || str_contains($textToSearch, 'av.');
                    $prefix = $isAv ? 'Avenida ' : 'Calle ';
                    $roadName = $prefix . ucwords($nameCandidate);
                }
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
            'source'         => 'nullable|string|max:255',
            'location_type'  => 'nullable|string|max:255',
            'is_fatal'     => 'nullable|boolean',
            'fuente_nombre' => 'nullable|string|max:255',
            'fuente_url'   => 'nullable|url',
            'verificado'   => 'nullable|boolean',
            'event_date'   => 'nullable|date',
            'source_publish_date' => 'nullable|date',
            'victim_names'   => 'nullable|string',
            'has_car'        => 'nullable|boolean',
            'has_pickup'     => 'nullable|boolean',
            'has_utility'    => 'nullable|boolean',
            'has_motorcycle' => 'nullable|boolean',
            'has_truck'      => 'nullable|boolean',
            'has_bus'        => 'nullable|boolean',
            'has_pedestrian' => 'nullable|boolean',
            'has_bicycle'    => 'nullable|boolean',
        ]);

        // Buscar o crear la categoría según la etiqueta
        $category = \App\Models\Category::firstOrCreate(
            ['slug' => \Illuminate\Support\Str::slug($validated['etiqueta'])],
            ['name' => ucfirst($validated['etiqueta'])]
        );

        // Prevenir duplicados directos (Misma URL o Mismo Título) o actualizar precisión si es re-evaluado
        if (!empty($validated['fuente_url'])) {
            $existing = Incident::where('source_url', $validated['fuente_url'])->first();
            if ($existing) {
                $existingIsApprox = (bool) $existing->is_approximate;
                $newIsApprox = (bool) ($validated['is_approximate'] ?? false);
                
                $precisionRanks = [
                    'ROOFTOP' => 4,
                    'RANGE_INTERPOLATED' => 3,
                    'GEOMETRIC_CENTER' => 2,
                    'APPROXIMATE' => 1
                ];
                $existingRank = $precisionRanks[$existing->location_type ?? 'GEOMETRIC_CENTER'] ?? 2;
                $newRank = $precisionRanks[$validated['location_type'] ?? 'GEOMETRIC_CENTER'] ?? 2;
                
                $updateLocation = false;
                if ($newRank > $existingRank) {
                    $updateLocation = true;
                } elseif ($existingIsApprox && !$newIsApprox) {
                    $updateLocation = true;
                }
                
                if ($updateLocation) {
                    $existing->update([
                        'latitude'       => $validated['latitud'],
                        'longitude'      => $validated['longitud'],
                        'is_approximate' => $newIsApprox,
                        'source'         => $validated['source'] ?? 'google',
                        'location_type'  => $validated['location_type'] ?? 'GEOMETRIC_CENTER',
                    ]);
                    
                    return response()->json([
                        'message' => 'Incidente existente actualizado con precisión de ubicación mejorada',
                        'incident' => $existing
                    ], 200);
                }
                
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
            // Quitar prefijos comunes (villa, barrio, bº, b°, vº, v°, etc.)
            $core = preg_replace('/^(b[º°\.]|villa|v[º°\.]|paraje)\s+/', '', $core);
            $locality->core_name_cleaned = trim($core);
            return $locality;
        })->sortByDesc(function ($locality) {
            return strlen($locality->core_name_cleaned);
        });

        // Obtener nombres de todos los departamentos en minúscula para evitar colisiones
        $departmentNamesLower = $departments->map(function ($d) {
            return $this->normalizeText($d->name);
        })->toArray();

        // 1. Buscar localidad en el texto (mayor especificidad)
        foreach ($localitiesWithCoreName as $locality) {
            $coreName = $locality->core_name_cleaned;
            if (strlen($coreName) > 3 && str_contains($textToSearch, $coreName)) {
                // Evitar colisión si el nombre de la localidad coincide con el de un departamento.
                // (ej: "sarmiento" de "Villa Sarmiento", "san martin" de "Villa San Martín").
                // En este caso, exigir el nombre completo normalizado de la localidad en el texto.
                if (in_array($coreName, $departmentNamesLower)) {
                    $normalizedFullName = $this->normalizeText($locality->name);
                    if (!str_contains($textToSearch, $normalizedFullName)) {
                        continue;
                    }
                }
                
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

        // --- Resolución de Víctimas (Gemini o Fallback Regex) ---
        $victimNames = $request->input('victim_names');
        $namesToSearch = [];
        if (!is_null($victimNames) && $victimNames !== '') {
            if (is_array($victimNames)) {
                $namesToSearch = $victimNames;
                $victimNames = implode(', ', $namesToSearch);
            } else {
                $namesToSearch = array_filter(array_map('trim', explode(',', $victimNames)));
            }
        } else {
            $newExtracted = $this->extractProperNouns(($validated['titulo'] ?? '') . ' ' . ($validated['descripcion'] ?? ''));
            $namesToSearch = !empty($newExtracted['full_names']) ? $newExtracted['full_names'] : [];
            $victimNames = !empty($newExtracted['full_names']) ? implode(', ', $newExtracted['full_names']) : null;
        }

        // --- Clasificación de Movilidades (Vehículos/Actores) ---
        $vehicles = [];
        foreach (['has_car', 'has_pickup', 'has_utility', 'has_motorcycle', 'has_truck', 'has_bus', 'has_pedestrian', 'has_bicycle'] as $field) {
            $vehicles[$field] = $request->has($field) ? (bool) $request->input($field) : null;
        }
        
        // Si no se pasaron todos o algunos, resolver con la función local
        if (collect($vehicles)->every(fn($v) => is_null($v))) {
            $vehicles = $this->resolveVehicleParticipation(
                $validated['titulo'] ?? '',
                $validated['descripcion'] ?? ''
            );
        } else {
            // Rellenar con false los nulls restantes
            foreach ($vehicles as $key => $val) {
                if (is_null($val)) {
                    $vehicles[$key] = false;
                }
            }
        }

        // --- Lógica de Asociación de Fallecimiento Post-Evento ---
        // Si el reporte actual es fatal, intentamos vincularlo a un accidente previo
        if (!empty($validated['is_fatal'])) {
            $isAccident = collect(['choque', 'vuelco', 'atropello', 'accidente', 'transito'])
                ->contains(fn($word) => str_contains(strtolower($validated['etiqueta']), $word));

            if ($isAccident) {

                $similarIncident = null;

                // 1. Primero intentar buscar por coincidencia de nombre de víctima en una ventana amplia de 45 días
                if (!empty($namesToSearch)) {
                    $candidates = Incident::where('is_fatal', '!=', 1)
                        ->where('event_date', '>=', now()->subDays(45))
                        ->get();

                    foreach ($candidates as $candidate) {
                        $candidateNames = array_map('trim', explode(',', $candidate->victim_names ?? ''));
                        foreach ($namesToSearch as $name) {
                            $nameLower = mb_strtolower($name, 'UTF-8');
                            foreach ($candidateNames as $cName) {
                                $cNameLower = mb_strtolower($cName, 'UTF-8');
                                if (!empty($nameLower) && !empty($cNameLower)) {
                                    // Coincidencia exacta o contenida (ej: "Melani" con "Melani Desseff")
                                    if ($nameLower === $cNameLower || str_contains($cNameLower, $nameLower) || str_contains($nameLower, $cNameLower)) {
                                        $similarIncident = $candidate;
                                        break 2;
                                    }
                                }
                            }
                        }
                    }
                }

                // 2. Si no se encontró coincidencia por nombre de víctima, usar el fallback geográfico tradicional de 15 días
                if (!$similarIncident) {
                    $similarIncident = Incident::where('is_fatal', '!=', 1)
                        ->where('event_date', '>=', now()->subDays(15))
                        ->whereBetween('latitude', [$validated['latitud'] - 0.01, $validated['latitud'] + 0.01])
                        ->whereBetween('longitude', [$validated['longitud'] - 0.01, $validated['longitud'] + 0.01])
                        ->first();
                }

                if ($similarIncident) {
                    $similarIncident->update([
                        'is_fatal' => true,
                        'description' => $similarIncident->description . "\n\n[ACTUALIZACIÓN FATAL]: " . $validated['titulo'] . " (Fuente: " . ($validated['fuente_url'] ?? 'N/A') . ")",
                        'source_publish_date' => $validated['source_publish_date'] ?? now(),
                        'updated_at' => now(),
                    ]);

                    // Si hay nuevos nombres detectados que no estaban en el original, anexarlos
                    if (!empty($namesToSearch)) {
                        $existingNames = array_map('trim', explode(',', $similarIncident->victim_names ?? ''));
                        $existingNames = array_filter($existingNames);
                        $mergedNames = $existingNames;
                        foreach ($namesToSearch as $newName) {
                            $alreadyExists = false;
                            $newNameLower = mb_strtolower($newName, 'UTF-8');
                            foreach ($mergedNames as $key => $existingName) {
                                $existingNameLower = mb_strtolower($existingName, 'UTF-8');
                                if ($existingNameLower === $newNameLower || str_contains($newNameLower, $existingNameLower)) {
                                    $mergedNames[$key] = $newName; 
                                    $alreadyExists = true;
                                    break;
                                } elseif (str_contains($existingNameLower, $newNameLower)) {
                                    $alreadyExists = true;
                                    break;
                                }
                            }
                            if (!$alreadyExists) {
                                $mergedNames[] = $newName;
                            }
                        }
                        $similarIncident->update([
                            'victim_names' => !empty($mergedNames) ? implode(', ', array_unique($mergedNames)) : null
                        ]);
                    }

                    // Check if event was yesterday or older
                    $eventDateObj = \Carbon\Carbon::parse($similarIncident->event_date);
                    if ($eventDateObj->isBefore(today())) {
                        \Illuminate\Support\Facades\DB::table('incident_notifications')->insert([
                            'incident_id' => $similarIncident->id,
                            'type' => 'fatal_yesterday',
                            'created_at' => now(),
                            'updated_at' => now()
                        ]);
                    }

                    return response()->json([
                        'message' => 'Incidente previo actualizado a estado FATAL',
                        'incident' => $similarIncident
                    ], 200);
                }
            }
        }

        // ---------------------------------------------------------

        // --- Lógica de Duplicados Cercanos (Fuzzy) y Fusión Inteligente ---
        // Buscamos si ya hay un incidente de la misma categoría en un radio de ~1.5km
        // o si comparten nombres propios únicos (ej: nombres de víctimas) en una ventana de ±2 días.
        $eventDate = \Carbon\Carbon::parse($validated['event_date'] ?? now());
        $candidates = Incident::where('category_id', $category->id)
            ->whereBetween('event_date', [
                $eventDate->copy()->subDays(2),
                $eventDate->copy()->addDays(2)
            ])
            ->get();



        $fuzzyDuplicate = null;
        foreach ($candidates as $candidate) {
            // 1. Verificar cercanía por coordenadas (~1.5km en grados de latitud/longitud)
            // IMPORTANTE: NO permitir fusión por distancia si alguno de los dos reportes es aproximado (is_approximate = 1),
            // ya que los fallbacks geográficos generales colisionarían siempre en el mismo punto de la cabecera departamental.
            $isClose = false;
            $existingIsApprox = (bool) $candidate->is_approximate;
            $newIsApprox = (bool) ($validated['is_approximate'] ?? false);

            if (!$existingIsApprox && !$newIsApprox) {
                $latDiff = abs($candidate->latitude - $validated['latitud']);
                $lngDiff = abs($candidate->longitude - $validated['longitud']);
                $isClose = ($latDiff <= 0.015 && $lngDiff <= 0.015);
            }

            // 2. Verificar si comparten nombres propios específicos (víctimas/detalles únicos)
            $text1 = ($validated['titulo'] ?? '') . ' ' . ($validated['descripcion'] ?? '');
            $text2 = ($candidate->title ?? '') . ' ' . ($candidate->description ?? '');
            $sharesProperNoun = $this->shareUniqueProperNoun($text1, $text2);

            if ($isClose || $sharesProperNoun) {
                $fuzzyDuplicate = $candidate;
                break;
            }
        }


        if ($fuzzyDuplicate) {
            $existingHasLocality = !empty($fuzzyDuplicate->locality_id);
            $newHasLocality = !empty($localityId);
            
            $existingIsApprox = (bool) $fuzzyDuplicate->is_approximate;
            $newIsApprox = (bool) ($validated['is_approximate'] ?? false);

            $newLocationIsBetter = false;

            // Comparar precisión de location_type
            $precisionRanks = [
                'ROOFTOP' => 4,
                'RANGE_INTERPOLATED' => 3,
                'GEOMETRIC_CENTER' => 2,
                'APPROXIMATE' => 1
            ];
            
            $existingRank = $precisionRanks[$fuzzyDuplicate->location_type ?? 'GEOMETRIC_CENTER'] ?? 2;
            $newRank = $precisionRanks[$validated['location_type'] ?? 'GEOMETRIC_CENTER'] ?? 2;

            if ($newRank > $existingRank) {
                $newLocationIsBetter = true;
            } elseif ($existingIsApprox && !$newIsApprox) {
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
                $updateData['source'] = $validated['source'] ?? 'nominatim';
                $updateData['location_type'] = $validated['location_type'] ?? 'GEOMETRIC_CENTER';
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

            // Fusión inteligente de nombres de víctimas
            $existingNames = array_map('trim', explode(',', $fuzzyDuplicate->victim_names ?? ''));
            $existingNames = array_filter($existingNames); // remover vacíos
            
            $newNames = $namesToSearch;

            $mergedNames = $existingNames;
            foreach ($newNames as $newName) {
                $alreadyExists = false;
                $newNameLower = mb_strtolower($newName, 'UTF-8');
                
                foreach ($mergedNames as $key => $existingName) {
                    $existingNameLower = mb_strtolower($existingName, 'UTF-8');
                    
                    if ($existingNameLower === $newNameLower) {
                        $alreadyExists = true;
                        break;
                    }
                    
                    // Si el nombre existente es una versión más corta (ej: "Melani")
                    // y el nuevo es más completo (ej: "Melani Desseff"), actualizarlo
                    if (str_contains($newNameLower, $existingNameLower)) {
                        $mergedNames[$key] = $newName; 
                        $alreadyExists = true;
                        break;
                    }
                    
                    // Si el nuevo nombre es más corto (ej: "Melani") y el existente es completo ("Melani Desseff")
                    if (str_contains($existingNameLower, $newNameLower)) {
                        $alreadyExists = true; 
                        break;
                    }
                }
                
                if (!$alreadyExists) {
                    $mergedNames[] = $newName;
                }
            }
            
            $updateData['victim_names'] = !empty($mergedNames) ? implode(', ', array_unique($mergedNames)) : null;

            // Preservación Cronológica: Conservar la fecha más antigua (real del suceso)
            $existingEventDate = \Carbon\Carbon::parse($fuzzyDuplicate->event_date);
            if ($eventDate->lt($existingEventDate)) {
                $updateData['event_date'] = $eventDate;
            }

            // Si el nuevo es fatal y el existente no, actualizarlo
            if (($validated['is_fatal'] ?? false) && !$fuzzyDuplicate->is_fatal) {
                $updateData['is_fatal'] = true;
                
                // Si el evento ocurrió ayer o antes, generar notificación
                if ($existingEventDate->isBefore(today())) {
                    \Illuminate\Support\Facades\DB::table('incident_notifications')->insert([
                        'incident_id' => $fuzzyDuplicate->id,
                        'type' => 'fatal_yesterday',
                        'created_at' => now(),
                        'updated_at' => now()
                    ]);
                }
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
            'source'         => $validated['source'] ?? 'nominatim',
            'location_type'  => $validated['location_type'] ?? 'GEOMETRIC_CENTER',
            'is_fatal'       => $validated['is_fatal'] ?? null,
            'status'         => 'Published',
            'event_date'     => $eventDate,
            'locality_id'    => $localityId,
            'department_id'  => $departmentId,
            'province_id'    => $provinceId,
            'road_type'      => $roadType,
            'road_name'      => $roadName,
            'victim_names'   => $victimNames,
            'has_car'        => $vehicles['has_car'],
            'has_pickup'     => $vehicles['has_pickup'],
            'has_utility'    => $vehicles['has_utility'],
            'has_motorcycle' => $vehicles['has_motorcycle'],
            'has_truck'      => $vehicles['has_truck'],
            'has_bus'        => $vehicles['has_bus'],
            'has_pedestrian' => $vehicles['has_pedestrian'],
            'has_bicycle'    => $vehicles['has_bicycle'],
            'source_publish_date' => $validated['source_publish_date'] ?? now(),
            'reported_at'    => now(),
        ]);

        // Create notification if the new incident is fatal and from a past date
        if ($incident->is_fatal && \Carbon\Carbon::parse($incident->event_date)->isBefore(today())) {
            \Illuminate\Support\Facades\DB::table('incident_notifications')->insert([
                'incident_id' => $incident->id,
                'type' => 'fatal_yesterday',
                'created_at' => now(),
                'updated_at' => now()
            ]);
        }

        return response()->json([
            'message' => 'Incidente registrado correctamente',
            'incident' => $incident
        ], 201);
    }

    /**
     * Extrae nombres propios de personas (nombres completos y palabras singulares) de un texto,
     * eliminando referencias a calles/avenidas y filtrando una lista negra exhaustiva.
     */
    private function extractProperNouns(string $text): array
    {
        $blacklist = [
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'este', 'esta', 'estos', 'estas',
            'ese', 'esa', 'esos', 'esas', 'aquel', 'aquella', 'con', 'sin', 'por', 'para', 'como',
            'cuando', 'donde', 'quien', 'cual', 'cuyo', 'pero', 'mas', 'sino', 'aunque', 'porque',
            'desde', 'hasta', 'entre', 'sobre', 'tras', 'durante', 'segun', 'contra', 'hacia',
            'policia', 'justicia', 'hospital', 'rawson', 'sanjuan', 'argentina', 'ufi',
            'fiscal', 'fiscalia', 'comisaria', 'medicos', 'doctor', 'enfermera', 'enfermero',
            'joven', 'hombre', 'mujer', 'chico', 'chica', 'menor', 'abuelo', 'abuela',
            'mañana', 'tarde', 'noche', 'lunes', 'martes', 'miercoles', 'jueves', 'viernes',
            'sabado', 'domingo', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
            'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
            'capital', 'rawson', 'rivadavia', 'chimbas', 'santa', 'lucia', 'pocito',
            'caucete', 'jachal', 'albardon', 'sarmiento', 'angaco', 'iglesia', 'calinga',
            'valle', 'fertil', 'ullum', 'zonda', 'avenida', 'calle', 'ruta', 'esquina',
            'barrio', 'villa', 'paraje', 'interseccion', 'choque', 'vuelco', 'colision',
            'fuente', 'diario', 'prensa', 'noticias', 'telesol', 'sanjuan8', 'huarpe', 'cuyo',
            'personal', 'efectivos', 'personal policial', 'policial', 'ambulancia', 'salud',
            'urgencias', 'terapia', 'intensiva', 'sanatorio', 'clinica', 'chofer', 'conductor',
            'pasajero', 'acompañante', 'peaton', 'motociclista', 'ciclista', 'camionero',
            'detenido', 'aprehendido', 'imputado', 'comisario', 'principal', 'oficial',
            'juez', 'ayudante', 'delitos', 'especiales', 'transito', 'gendarmeria', 'bomberos',
            'patrullero', 'vehiculo', 'motocicleta', 'automovil', 'camioneta', 'colectivo'
        ];

        // 1. Limpieza de calles y rutas para evitar falsos positivos
        // Limpiar "calle/avenida/av/ruta..." seguido de nombres propios
        $cleanText = preg_replace('/\b(calle|calles|avenida|avenidas|av\.?|ruta|bulevar|pasaje|esquina|intersección|cruce|calle lateral)\s+([A-Z][a-zA-ZáéíóúÁÉÍÓÚñÑ0-9]+(?:\s+(?:de\s+la|de|del|y|e|o)\s+[A-Z][a-zA-ZáéíóúÁÉÍÓÚñÑ]+)?)/iu', '', $text);
        
        // Limpiar "ruta [0-9]+"
        $cleanText = preg_replace('/\bruta\s+\d+/iu', '', $cleanText);

        // 2. Extraer parejas consecutivas de palabras capitalizadas (Nombres Completos: "Melani Desseff")
        preg_match_all('/\b([A-Z][a-záéíóúÁÉÍÓÚñÑ]+)\s+([A-Z][a-záéíóúÁÉÍÓÚñÑ]+)\b/u', $cleanText, $pairs);
        
        $fullNames = [];
        if (!empty($pairs[0])) {
            foreach ($pairs[0] as $match) {
                $words = preg_split('/\s+/', $match);
                if (count($words) < 2) {
                    continue;
                }
                $w1Lower = mb_strtolower($words[0], 'UTF-8');
                $w2Lower = mb_strtolower($words[1], 'UTF-8');
                
                // Exigir que ninguno esté en la lista negra y que tengan longitud suficiente
                if (!in_array($w1Lower, $blacklist) && !in_array($w2Lower, $blacklist)) {
                    if (mb_strlen($words[0]) >= 3 && mb_strlen($words[1]) >= 3) {
                        $fullNames[] = trim($match);
                    }
                }
            }
        }

        // 3. Extraer palabras capitalizadas individuales altamente singulares
        // (excluyendo el inicio de oraciones para evitar falsas capitalizaciones)
        preg_match_all('/(?<!\.\s)(?<!\A)\b([A-Z][a-záéíóúÁÉÍÓÚñÑ]+)\b/u', $cleanText, $singles);
        
        $singleNames = [];
        if (!empty($singles[1])) {
            foreach ($singles[1] as $w) {
                $wLower = mb_strtolower($w, 'UTF-8');
                if (!in_array($wLower, $blacklist) && mb_strlen($wLower) >= 4) {
                    $singleNames[] = $w;
                }
            }
        }

        return [
            'full_names' => array_values(array_unique($fullNames)),
            'single_names' => array_values(array_unique($singleNames))
        ];
    }

    /**
     * Compara dos textos y determina si comparten nombres propios específicos (víctimas/accidentados)
     * ignorando calles y palabras comunes de la lista negra.
     */
    private function shareUniqueProperNoun(string $text1, string $text2): bool
    {
        $res1 = $this->extractProperNouns($text1);
        $res2 = $this->extractProperNouns($text2);

        // 1. Comparar nombres completos (Coincidencia exacta de Nombre y Apellido)
        // Ej: "Melani Desseff" en ambos textos
        foreach ($res1['full_names'] as $name1) {
            $n1Lower = mb_strtolower($name1, 'UTF-8');
            foreach ($res2['full_names'] as $name2) {
                $n2Lower = mb_strtolower($name2, 'UTF-8');
                if ($n1Lower === $n2Lower) {
                    return true;
                }
            }
        }

        // 2. Comparar apellidos/nombres individuales altamente singulares
        // Si comparten un apellido muy raro y característico, ej: "Desseff" o "Deseff"
        foreach ($res1['single_names'] as $s1) {
            $s1Lower = mb_strtolower($s1, 'UTF-8');
            foreach ($res2['single_names'] as $s2) {
                $s2Lower = mb_strtolower($s2, 'UTF-8');
                
                if ($s1Lower === $s2Lower) {
                    return true;
                }
            }
        }

        return false;
    }
}

