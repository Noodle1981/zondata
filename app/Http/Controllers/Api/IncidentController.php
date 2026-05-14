<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Incident;
use Illuminate\Http\Request;

class IncidentController extends Controller
{
    public function index(Request $request)
    {
        $query = Incident::with('category')
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

        // Prevenir duplicados (Misma URL o Mismo Título)
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

        // --- Lógica de Asociación de Fallecimiento Post-Evento ---
        // Si el reporte actual es fatal, intentamos vincularlo a un accidente previo
        if ($validated['is_fatal']) {
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

        // --- Lógica de Duplicados Cercanos (Fuzzy) ---
        // Si ya hay un incidente de la misma categoría en un radio de ~1km en los últimos 2 días,
        // lo consideramos el mismo evento reportado por otro medio.
        $fuzzyDuplicate = Incident::where('category_id', $category->id)
            ->whereBetween('event_date', [
                \Carbon\Carbon::parse($validated['event_date'])->subDays(2),
                \Carbon\Carbon::parse($validated['event_date'])->addDays(2)
            ])
            ->whereBetween('latitude', [$validated['latitud'] - 0.01, $validated['latitud'] + 0.01])
            ->whereBetween('longitude', [$validated['longitud'] - 0.01, $validated['longitud'] + 0.01])
            ->first();

        if ($fuzzyDuplicate) {
            return response()->json([
                'message' => 'Incidente ya registrado por otro medio (Cercanía/Categoría)',
                'incident' => $fuzzyDuplicate
            ], 200);
        }
        // ---------------------------------------------

        $incident = Incident::create([
            'category_id'    => $category->id,
            'title'          => $validated['titulo'],
            'description'    => $validated['descripcion'],
            'source_name'    => $validated['fuente_nombre'],
            'source_url'     => $validated['fuente_url'],
            'latitude'       => $validated['latitud'],
            'longitude'      => $validated['longitud'],
            'is_approximate' => $validated['is_approximate'] ?? false,
            'is_fatal'       => $validated['is_fatal'] ?? null,
            'status'         => 'Published',
            'event_date'     => $validated['event_date'] ?? now(),
        ]);

        return response()->json([
            'message' => 'Incidente registrado correctamente',
            'incident' => $incident
        ], 201);
    }
}
