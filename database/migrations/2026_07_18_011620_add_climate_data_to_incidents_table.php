<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('incidents', function (Blueprint $table) {
            $table->string('phenomenon_type')->nullable();     // 'zonda', 'viento_sur', etc.
            $table->boolean('wind_cause')->nullable();         // el viento fue la causa
            $table->float('temp_c')->nullable();               // temperatura °C
            $table->float('humidity_pct')->nullable();         // humedad relativa %
            $table->float('wind_speed_kmh')->nullable();       // velocidad del viento
            $table->integer('wind_direction_deg')->nullable(); // dirección del viento
            $table->float('precipitation_mm')->nullable();     // precipitación mm
            $table->integer('uv_index')->nullable();           // índice UV
            $table->string('weather_code')->nullable();        // código WMO
            $table->string('enso_phase')->nullable();          // 'niño', 'niña', 'neutro'
            $table->float('hectares_burned')->nullable();      // solo incendios
            $table->boolean('climate_enriched')->default(false);
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('incidents', function (Blueprint $table) {
            $table->dropColumn([
                'phenomenon_type',
                'wind_cause',
                'temp_c',
                'humidity_pct',
                'wind_speed_kmh',
                'wind_direction_deg',
                'precipitation_mm',
                'uv_index',
                'weather_code',
                'enso_phase',
                'hectares_burned',
                'climate_enriched'
            ]);
        });
    }
};
