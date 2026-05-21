<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use App\Models\ScraperSource;

class ScraperSourceSeeder extends Seeder
{
    /**
     * Pobla la tabla scraper_sources con todos los medios de San Juan.
     * Se ejecuta automáticamente en cada php artisan migrate:fresh --seed
     * y desde el panel /admin para restaurar las reglas por defecto.
     */
    public function run(): void
    {
        // Limpiar antes de repoblar para evitar duplicados en re-seeds
        ScraperSource::truncate();

        $sources = [
            // ─── Medios RSS ────────────────────────────────────────────────
            [
                'domain'               => 'diariodecuyo.com.ar',
                'name'                 => 'Diario de Cuyo',
                'type'                 => 'rss',
                'scrape_urls'          => [
                    'https://diariodecuyo.com.ar/rss/pages/policiales.xml',
                    'https://diariodecuyo.com.ar/rss/pages/san-juan.xml',
                ],
                'sanitize_exclusions'  => ['Hospital Rawson'],
                'ignore_terms'         => [],
                'deep_fetch'           => true,
                'duplicate_check'      => true,
                'active'               => true,
                'priority'             => 10,
                'fallback_context'     => 'San Juan, Argentina',
            ],
            [
                'domain'               => 'tiempodesanjuan.com',
                'name'                 => 'Tiempo de San Juan',
                'type'                 => 'rss',
                'scrape_urls'          => [
                    'https://www.tiempodesanjuan.com/rss/pages/Policiales.xml',
                    'https://www.tiempodesanjuan.com/rss/pages/home.xml',
                ],
                'sanitize_exclusions'  => ['Hospital Rawson'],
                'ignore_terms'         => [],
                'deep_fetch'           => true,
                'duplicate_check'      => true,
                'active'               => true,
                'priority'             => 9,
                'fallback_context'     => 'San Juan, Argentina',
            ],
            [
                'domain'               => 'diariohuarpe.com',
                'name'                 => 'Diario Huarpe',
                'type'                 => 'rss',
                'scrape_urls'          => [
                    'https://www.diariohuarpe.com/rss/policiales.xml',
                    'https://www.diariohuarpe.com/rss/portada.xml',
                ],
                'sanitize_exclusions'  => [],
                'ignore_terms'         => [],
                'deep_fetch'           => true,
                'duplicate_check'      => true,
                'active'               => true,
                'priority'             => 9,
                'fallback_context'     => 'San Juan, Argentina',
            ],
            [
                'domain'               => 'nuevodiariosanjuan.com.ar',
                'name'                 => 'Nuevo Diario',
                'type'                 => 'rss',
                'scrape_urls'          => ['https://www.nuevodiariosanjuan.com.ar/feed'],
                'sanitize_exclusions'  => [],
                'ignore_terms'         => [],
                'deep_fetch'           => true,
                'duplicate_check'      => true,
                'active'               => true,
                'priority'             => 7,
                'fallback_context'     => 'San Juan, Argentina',
            ],
            [
                'domain'               => 'diariolaprovinciasj.com',
                'name'                 => 'Diario La Provincia',
                'type'                 => 'rss',
                'scrape_urls'          => ['https://www.diariolaprovinciasj.com/rss'],
                'sanitize_exclusions'  => [],
                'ignore_terms'         => [],
                'deep_fetch'           => true,
                'duplicate_check'      => true,
                'active'               => true,
                'priority'             => 7,
                'fallback_context'     => 'San Juan, Argentina',
            ],
            [
                'domain'               => 'canal4sanjuan.com.ar',
                'name'                 => 'Canal 4 San Juan',
                'type'                 => 'rss',
                'scrape_urls'          => ['https://canal4sanjuan.com.ar/feed/'],
                'sanitize_exclusions'  => [],
                'ignore_terms'         => [],
                'deep_fetch'           => true,
                'duplicate_check'      => true,
                'active'               => true,
                'priority'             => 7,
                'fallback_context'     => 'San Juan, Argentina',
            ],
            [
                'domain'               => 'canal13sanjuan.com',
                'name'                 => 'Diario 13 San Juan',
                'type'                 => 'rss',
                'scrape_urls'          => ['https://www.canal13sanjuan.com/rss'],
                'sanitize_exclusions'  => [],
                'ignore_terms'         => [],
                'deep_fetch'           => true,
                'duplicate_check'      => true,
                'active'               => true,
                'priority'             => 7,
                'fallback_context'     => 'San Juan, Argentina',
            ],
            [
                'domain'               => 'nuevomundosj.com.ar',
                'name'                 => 'Nuevo Mundo',
                'type'                 => 'rss',
                'scrape_urls'          => ['https://nuevomundosj.com.ar/category/policiales/feed/'],
                'sanitize_exclusions'  => [],
                'ignore_terms'         => [],
                'deep_fetch'           => true,
                'duplicate_check'      => true,
                'active'               => true,
                'priority'             => 6,
                'fallback_context'     => 'San Juan, Argentina',
            ],
            [
                'domain'               => 'telesoldiario.com',
                'name'                 => 'Telesol Diario',
                'type'                 => 'rss',
                'scrape_urls'          => ['https://www.telesoldiario.com/rss'],
                'sanitize_exclusions'  => [],
                'ignore_terms'         => [],
                'deep_fetch'           => true,
                'duplicate_check'      => true,
                'active'               => true,
                'priority'             => 6,
                'fallback_context'     => 'San Juan, Argentina',
            ],
            [
                'domain'               => 'sanjuan8.com',
                'name'                 => 'San Juan 8',
                'type'                 => 'rss',
                'scrape_urls'          => ['https://www.sanjuan8.com/rss'],
                'sanitize_exclusions'  => ['Hospital Rawson'],
                'ignore_terms'         => [],
                'deep_fetch'           => true,
                'duplicate_check'      => true,
                'active'               => true,
                'priority'             => 8,
                'fallback_context'     => 'San Juan, Argentina',
            ],

            // ─── Medios HTML (scraping directo de página) ──────────────────
            [
                'domain'               => 'diariomovil.info',
                'name'                 => 'Diario Móvil',
                'type'                 => 'html',
                'scrape_urls'          => ['https://diariomovil.info/categoria/4/san-juan'],
                'article_selector'     => '<div[^>]*class=\"[^\"]*post[^\"]*\"[^>]*>.*?<a[^>]*href=\"([^\"]+)\"[^>]*>.*?<h[23][^>]*class=\"[^\"]*titulo[^\"]*\"[^>]*>(.*?)</h[23]>.*?<div[^>]*class=\"[^\"]*resumen[^\"]*\"[^>]*>(.*?)</div>',
                'sanitize_exclusions'  => ['Hospital Rawson'],
                'ignore_terms'         => [],
                'deep_fetch'           => true,
                'duplicate_check'      => true,
                'active'               => true,
                'priority'             => 5,
                'fallback_context'     => 'San Juan, Argentina',
            ],
            [
                'domain'               => '0264noticias.com.ar',
                'name'                 => '0264 Noticias',
                'type'                 => 'html',
                'scrape_urls'          => ['https://www.0264noticias.com.ar/policiales'],
                'article_selector'     => '<a[^>]*class=\"[^\"]*w-full[^\"]*\"[^>]*href=\"(/noticias/[^\"]+)\"[^>]*>(?:\s*<h3[^>]*>.*?</h3>)?\s*<h2[^>]*>(.*?)</h2>\s*</a>',
                'sanitize_exclusions'  => ['Hospital Rawson'],
                'ignore_terms'         => [],
                'deep_fetch'           => true,
                'duplicate_check'      => true,
                'active'               => true,
                'priority'             => 5,
                'fallback_context'     => 'San Juan, Argentina',
            ],
        ];

        foreach ($sources as $source) {
            ScraperSource::create($source);
        }

        $this->command->info('✅ ScraperSourceSeeder: ' . count($sources) . ' fuentes cargadas.');
    }
}
