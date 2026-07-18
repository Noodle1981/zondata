<?php

namespace App\Http\Controllers\Admin;

use Backpack\CRUD\app\Http\Controllers\CrudController;
use Backpack\CRUD\app\Library\CrudPanel\CrudPanelFacade as CRUD;

class ScraperSourceCrudController extends CrudController
{
    use \Backpack\CRUD\app\Http\Controllers\Operations\ListOperation;
    use \Backpack\CRUD\app\Http\Controllers\Operations\CreateOperation;
    use \Backpack\CRUD\app\Http\Controllers\Operations\UpdateOperation;
    use \Backpack\CRUD\app\Http\Controllers\Operations\DeleteOperation;
    use \Backpack\CRUD\app\Http\Controllers\Operations\ShowOperation;

    public function setup()
    {
        CRUD::setModel(\App\Models\ScraperSource::class);
        CRUD::setRoute(config('backpack.base.route_prefix') . '/scraper-source');
        CRUD::setEntityNameStrings('fuente de scraper', 'fuentes de scraper');
    }

    protected function setupListOperation()
    {
        CRUD::addColumn([
            'name' => 'name',
            'label' => 'Nombre',
        ]);

        CRUD::addColumn([
            'name' => 'domain',
            'label' => 'Dominio',
        ]);

        CRUD::addColumn([
            'name' => 'type',
            'label' => 'Tipo',
        ]);

        CRUD::addColumn([
            'name' => 'active',
            'label' => 'Activo',
            'type' => 'boolean',
        ]);

        CRUD::addColumn([
            'name' => 'priority',
            'label' => 'Prioridad',
            'type' => 'number',
        ]);

        CRUD::addColumn([
            'name' => 'status_indicator',
            'label' => 'Estado del Feed',
            'type' => 'html',
            'value' => function($entry) {
                if ($entry->is_broken) {
                    $err = e($entry->error_message ?? 'Error desconocido');
                    return '<span class="badge bg-danger text-white" style="padding: 5px 8px; font-weight: bold;" title="' . $err . '">⚠️ Roto</span>';
                }
                
                if ($entry->active && $entry->last_article_at) {
                    $days = \Carbon\Carbon::parse($entry->last_article_at)->diffInDays(now());
                    if ($days >= 7) {
                        return '<span class="badge bg-warning text-dark" style="padding: 5px 8px; font-weight: bold;" title="Última noticia: ' . $entry->last_article_at->format('d/m/Y') . ' (' . $days . ' días sin novedades). Posible feed desactualizado o roto.">⏳ Inactivo</span>';
                    }
                }
                
                return '<span class="badge bg-success text-white" style="padding: 5px 8px; font-weight: bold;">✅ Activo / OK</span>';
            }
        ]);

        CRUD::addColumn([
            'name' => 'last_scraped_at',
            'label' => 'Último Barrido',
            'type' => 'datetime',
        ]);

        CRUD::addColumn([
            'name' => 'last_article_at',
            'label' => 'Último Artículo',
            'type' => 'datetime',
        ]);
    }

    protected function setupCreateOperation()
    {
        CRUD::field('name')->label('Nombre');
        CRUD::field('domain')->label('Dominio');
        CRUD::field('type')->type('enum')->label('Tipo');
        CRUD::field('scrape_urls')->type('textarea')->label('URLs de Ingesta (JSON Array)')->default('[]');
        CRUD::field('article_selector')->type('text')->label('Selector de Artículo HTML (Regex, solo si tipo es HTML)');
        CRUD::field('active')->type('checkbox')->label('Activo')->default(true);
        CRUD::field('priority')->type('number')->label('Prioridad (1-10)')->default(5);
        CRUD::field('fallback_context')->type('text')->label('Contexto Geográfico Fallback')->default('San Juan, Argentina');
        CRUD::field('custom_context')->type('text')->label('Contexto Fijo (ej: Calingasta, San Juan, Argentina)');
        CRUD::field('deep_fetch')->type('checkbox')->label('Descargar Cuerpo Completo')->default(true);
        CRUD::field('duplicate_check')->type('checkbox')->label('Evitar Duplicados')->default(true);
    }

    protected function setupUpdateOperation()
    {
        $this->setupCreateOperation();
    }
}
