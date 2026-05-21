<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Tabla de fuentes del scraper RSS/HTML.
     * Cada fila es un medio de comunicación con su configuración completa.
     * Reemplaza el archivo scraper_rules.json y el zondata.db separado.
     */
    public function up(): void
    {
        Schema::create('scraper_sources', function (Blueprint $table) {
            $table->id();

            // Identificación del medio
            $table->string('domain')->unique()->comment('Dominio del medio, ej: diariodecuyo.com.ar');
            $table->string('name')->comment('Nombre legible del medio, ej: Diario de Cuyo');

            // Tipo de scraper
            $table->enum('type', ['rss', 'html'])->default('rss');

            // URLs a scrapear (puede ser más de una por medio)
            $table->json('scrape_urls')->comment('Array de URLs del feed RSS o páginas HTML a scrapear');

            // Configuraciones opcionales por fuente
            $table->json('sanitize_exclusions')->nullable()->comment('Frases a excluir antes de geocodificar, ej: ["Hospital Rawson"]');
            $table->json('ignore_terms')->nullable()->comment('Términos que hacen descartar el artículo, ej: ["publicidad"]');
            $table->text('article_selector')->nullable()->comment('Regex selector para fuentes HTML');
            $table->string('fallback_context')->default('San Juan, Argentina')->comment('Contexto geográfico de fallback');
            $table->string('custom_context')->nullable()->comment('Contexto geográfico fijo para este medio');

            // Flags de comportamiento
            $table->boolean('deep_fetch')->default(true)->comment('Si se descarga el cuerpo completo del artículo');
            $table->boolean('duplicate_check')->default(true)->comment('Si se verifica si la URL ya fue procesada');
            $table->boolean('active')->default(true)->comment('Si esta fuente está habilitada');

            // Prioridad de procesamiento (mayor = más importante)
            $table->unsignedTinyInteger('priority')->default(1);

            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('scraper_sources');
    }
};
