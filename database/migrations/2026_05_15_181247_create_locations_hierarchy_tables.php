<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('provinces', function (Blueprint $table) {
            $table->id();
            $table->string('name')->unique();
            $table->timestamps();
        });

        Schema::create('departments', function (Blueprint $table) {
            $table->id();
            $table->foreignId('province_id')->constrained()->onDelete('cascade');
            $table->string('name');
            $table->decimal('lat', 10, 7)->nullable();
            $table->decimal('lon', 10, 7)->nullable();
            $table->timestamps();
            $table->unique(['province_id', 'name']);
        });

        Schema::create('localities', function (Blueprint $table) {
            $table->id();
            $table->foreignId('department_id')->constrained()->onDelete('cascade');
            $table->string('name');
            $table->decimal('lat', 10, 7)->nullable();
            $table->decimal('lon', 10, 7)->nullable();
            $table->timestamps();
            $table->unique(['department_id', 'name']);
        });

        // Añadir relaciones a la tabla de incidentes si es necesario en el futuro
        Schema::table('incidents', function (Blueprint $table) {
            $table->foreignId('locality_id')->nullable()->constrained()->onDelete('set null');
            $table->foreignId('department_id')->nullable()->constrained()->onDelete('set null');
            $table->foreignId('province_id')->nullable()->constrained()->onDelete('set null');
        });
    }

    public function down(): void
    {
        Schema::table('incidents', function (Blueprint $table) {
            $table->dropForeign(['locality_id']);
            $table->dropForeign(['department_id']);
            $table->dropForeign(['province_id']);
            $table->dropColumn(['locality_id', 'department_id', 'province_id']);
        });
        Schema::dropIfExists('localities');
        Schema::dropIfExists('departments');
        Schema::dropIfExists('provinces');
    }
};
