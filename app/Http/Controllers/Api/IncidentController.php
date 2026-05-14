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
