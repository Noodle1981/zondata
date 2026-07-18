<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('scraper_sources', function (Blueprint $table) {
            $table->dateTime('last_scraped_at')->nullable()->comment('Última vez que se barrió esta fuente');
            $table->dateTime('last_article_at')->nullable()->comment('Último artículo nuevo encontrado en esta fuente');
            $table->boolean('is_broken')->default(false)->comment('Indica si la fuente tiene errores o está rota');
            $table->text('error_message')->nullable()->comment('Detalle del último error en el scraper');
        });
    }

    public function down(): void
    {
        Schema::table('scraper_sources', function (Blueprint $table) {
            $table->dropColumn(['last_scraped_at', 'last_article_at', 'is_broken', 'error_message']);
        });
    }
};
