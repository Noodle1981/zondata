<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Incident;
use Illuminate\Http\Request;

class IncidentController extends Controller
{
    public function index()
    {
        $incidents = Incident::with('category')
            ->where('status', 'Published')
            ->orderBy('event_date', 'desc')
            ->get();

        return response()->json($incidents);
    }

    public function store(Request $request)
    {
        // Validación básica
        $validated = $request->validate([
            'etiqueta' => 'required|string',
            'titulo' => 'required|string|max:255',
            'descripcion' => 'nullable|string',
            'latitud' => 'required|numeric',
            'longitud' => 'required|numeric',
            'is_approximate' => 'nullable|boolean',
            'fuente_nombre' => 'nullable|string|max:255',
            'fuente_url' => 'nullable|url',
            'verificado' => 'nullable|boolean',
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
            'category_id' => $category->id,
            'title' => $validated['titulo'],
            'description' => $validated['descripcion'],
            'source_name' => $validated['fuente_nombre'],
            'source_url' => $validated['fuente_url'],
            'latitude' => $validated['latitud'],
            'longitude' => $validated['longitud'],
            'is_approximate' => $validated['is_approximate'] ?? false,
            'status' => 'Published', // Por defecto publicado
            'event_date' => now(),
        ]);

        return response()->json([
            'message' => 'Incidente registrado correctamente',
            'incident' => $incident
        ], 201);
    }
}
