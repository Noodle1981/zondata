<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class ScraperSource extends Model
{
    protected $fillable = [
        'domain',
        'name',
        'type',
        'scrape_urls',
        'sanitize_exclusions',
        'ignore_terms',
        'article_selector',
        'fallback_context',
        'custom_context',
        'deep_fetch',
        'duplicate_check',
        'active',
        'priority',
    ];

    protected $casts = [
        'scrape_urls'          => 'array',
        'sanitize_exclusions'  => 'array',
        'ignore_terms'         => 'array',
        'deep_fetch'           => 'boolean',
        'duplicate_check'      => 'boolean',
        'active'               => 'boolean',
        'priority'             => 'integer',
    ];

    /**
     * Retorna solo las fuentes activas ordenadas por prioridad descendente.
     */
    public function scopeActive($query)
    {
        return $query->where('active', true)->orderByDesc('priority');
    }

    /**
     * Exporta esta fuente al formato que espera load_rules.py del scraper Python.
     * Estructura: { "type": "rss", "scrape_urls": [...], ... }
     */
    public function toScraperRule(): array
    {
        $rule = [
            'type'        => $this->type,
            'scrape_urls' => $this->scrape_urls ?? [],
            'deep_fetch'  => $this->deep_fetch,
            'duplicate_check' => $this->duplicate_check,
            'fallback_context' => $this->fallback_context,
            'priority'    => $this->priority,
        ];

        if (!empty($this->sanitize_exclusions)) {
            $rule['sanitize_exclusions'] = $this->sanitize_exclusions;
        }
        if (!empty($this->ignore_terms)) {
            $rule['ignore_terms'] = $this->ignore_terms;
        }
        if (!empty($this->article_selector)) {
            $rule['article_selector'] = $this->article_selector;
        }
        if (!empty($this->custom_context)) {
            $rule['custom_context'] = $this->custom_context;
        }

        return $rule;
    }
}
