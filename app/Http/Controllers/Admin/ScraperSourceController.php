<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\ScraperSource;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;

/**
 * CRUD de fuentes del scraper para el panel /admin.
 * Permite ver, crear, editar, activar/desactivar y restaurar las reglas
 * sin necesidad de tocar archivos JSON ni la base de datos manualmente.
 */
class ScraperSourceController extends Controller
{
    /** GET /admin/scraper-sources — Listar todas las fuentes */
    public function index(): JsonResponse
    {
        $sources = ScraperSource::orderByDesc('priority')->orderBy('name')->get();
        return response()->json($sources);
    }

    /** GET /admin/scraper-sources/{id} — Ver una fuente */
    public function show(ScraperSource $scraperSource): JsonResponse
    {
        return response()->json($scraperSource);
    }

    /** POST /admin/scraper-sources — Crear nueva fuente */
    public function store(Request $request): JsonResponse
    {
        $data = $request->validate([
            'domain'              => 'required|string|unique:scraper_sources,domain',
            'name'                => 'required|string|max:100',
            'type'                => 'required|in:rss,html',
            'scrape_urls'         => 'required|array|min:1',
            'scrape_urls.*'       => 'url',
            'sanitize_exclusions' => 'nullable|array',
            'ignore_terms'        => 'nullable|array',
            'article_selector'    => 'nullable|string',
            'fallback_context'    => 'nullable|string|max:100',
            'custom_context'      => 'nullable|string|max:100',
            'deep_fetch'          => 'boolean',
            'duplicate_check'     => 'boolean',
            'active'              => 'boolean',
            'priority'            => 'integer|min:1|max:10',
        ]);

        $source = ScraperSource::create($data);
        return response()->json($source, 201);
    }

    /** PUT /admin/scraper-sources/{id} — Actualizar fuente */
    public function update(Request $request, ScraperSource $scraperSource): JsonResponse
    {
        $data = $request->validate([
            'domain'              => 'sometimes|string|unique:scraper_sources,domain,' . $scraperSource->id,
            'name'                => 'sometimes|string|max:100',
            'type'                => 'sometimes|in:rss,html',
            'scrape_urls'         => 'sometimes|array|min:1',
            'scrape_urls.*'       => 'url',
            'sanitize_exclusions' => 'nullable|array',
            'ignore_terms'        => 'nullable|array',
            'article_selector'    => 'nullable|string',
            'fallback_context'    => 'nullable|string|max:100',
            'custom_context'      => 'nullable|string|max:100',
            'deep_fetch'          => 'boolean',
            'duplicate_check'     => 'boolean',
            'active'              => 'boolean',
            'priority'            => 'integer|min:1|max:10',
        ]);

        $scraperSource->update($data);
        return response()->json($scraperSource);
    }

    /** DELETE /admin/scraper-sources/{id} — Eliminar fuente */
    public function destroy(ScraperSource $scraperSource): JsonResponse
    {
        $scraperSource->delete();
        return response()->json(['message' => 'Fuente eliminada correctamente.']);
    }

    /**
     * PATCH /admin/scraper-sources/{id}/toggle — Activar o desactivar una fuente
     * Útil para deshabilitar temporalmente un medio sin eliminarlo.
     */
    public function toggle(ScraperSource $scraperSource): JsonResponse
    {
        $scraperSource->update(['active' => !$scraperSource->active]);
        $estado = $scraperSource->active ? 'activada' : 'desactivada';
        return response()->json([
            'message' => "Fuente {$estado} correctamente.",
            'active'  => $scraperSource->active,
        ]);
    }

    /**
     * POST /admin/scraper-sources/restore-defaults — Restaurar reglas por defecto
     * Ejecuta el ScraperSourceSeeder para repoblar la tabla con los valores originales.
     */
    public function restoreDefaults(): JsonResponse
    {
        try {
            \Artisan::call('db:seed', ['--class' => 'ScraperSourceSeeder', '--force' => true]);
            $count = ScraperSource::count();
            return response()->json([
                'message' => "Reglas restauradas correctamente. {$count} fuentes cargadas.",
                'sources' => ScraperSource::orderByDesc('priority')->get(),
            ]);
        } catch (\Exception $e) {
            return response()->json(['error' => 'No se pudieron restaurar las reglas: ' . $e->getMessage()], 500);
        }
    }

    /**
     * GET /admin/scraper-sources/export — Exportar en formato Python-compatible
     * Devuelve el JSON exacto que load_rules.py necesita para funcionar.
     */
    public function export(): JsonResponse
    {
        $sources = ScraperSource::active()->get();

        $rules = [
            'global' => [
                'fallback_context' => 'San Juan, Argentina',
                'duplicate_check'  => true,
                'deep_fetch'       => true,
            ],
            'sources' => [],
        ];

        foreach ($sources as $source) {
            $rules['sources'][$source->domain] = $source->toScraperRule();
        }

        return response()->json($rules);
    }
}
