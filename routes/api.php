<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\IncidentController;
use App\Http\Controllers\Admin\ScraperSourceController;

Route::get('/user', function (Request $request) {
    return $request->user();
})->middleware('auth:sanctum');

// ─── API pública de incidentes ────────────────────────────────────────────────
Route::get('/incidents/summary', [IncidentController::class, 'getSummary']);
Route::get('/incidents/notifications', [IncidentController::class, 'getNotifications']);
Route::get('/incidents', [IncidentController::class, 'index']);
Route::post('/incidents', [IncidentController::class, 'store']);

// ─── Admin: Gestión de fuentes del scraper ───────────────────────────────────
// GET    /api/admin/scraper-sources            → listar todas
// POST   /api/admin/scraper-sources            → crear nueva
// GET    /api/admin/scraper-sources/{id}       → ver una
// PUT    /api/admin/scraper-sources/{id}       → editar
// DELETE /api/admin/scraper-sources/{id}       → eliminar
// PATCH  /api/admin/scraper-sources/{id}/toggle → activar/desactivar
// POST   /api/admin/scraper-sources/restore-defaults → restaurar al seeder
// GET    /api/admin/scraper-sources/export     → exportar formato Python
Route::prefix('admin')->group(function () {
    Route::get('/scraper-sources/export', [ScraperSourceController::class, 'export']);
    Route::post('/scraper-sources/restore-defaults', [ScraperSourceController::class, 'restoreDefaults']);
    Route::patch('/scraper-sources/{scraperSource}/toggle', [ScraperSourceController::class, 'toggle']);
    Route::apiResource('/scraper-sources', ScraperSourceController::class);
});

