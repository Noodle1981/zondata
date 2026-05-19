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
            $table->boolean('has_car')->default(false)->index();
            $table->boolean('has_pickup')->default(false)->index();
            $table->boolean('has_utility')->default(false)->index();
            $table->boolean('has_motorcycle')->default(false)->index();
            $table->boolean('has_truck')->default(false)->index();
            $table->boolean('has_bus')->default(false)->index();
            $table->boolean('has_pedestrian')->default(false)->index();
            $table->boolean('has_bicycle')->default(false)->index();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('incidents', function (Blueprint $table) {
            $table->dropColumn([
                'has_car',
                'has_pickup',
                'has_utility',
                'has_motorcycle',
                'has_truck',
                'has_bus',
                'has_pedestrian',
                'has_bicycle'
            ]);
        });
    }
};
