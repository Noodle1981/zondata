<?php

namespace App\Models;

use Backpack\CRUD\app\Models\Traits\CrudTrait;
use Illuminate\Database\Eloquent\Model;

class Incident extends Model
{
    use CrudTrait;
    protected $fillable = [
        'category_id',
        'title',
        'description',
        'source_name',
        'source_url',
        'latitude',
        'longitude',
        'is_approximate',
        'source',
        'location_type',
        'is_fatal',
        'event_date',
        'status',
        'locality_id',
        'department_id',
        'province_id',
        'road_type',
        'road_name',
        'victim_names',
        'has_car',
        'has_pickup',
        'has_utility',
        'has_motorcycle',
        'has_truck',
        'has_bus',
        'has_pedestrian',
        'has_bicycle',
    ];

    protected $casts = [
        'event_date' => 'datetime',
        'is_approximate' => 'boolean',
        'is_fatal' => 'boolean',
        'has_car' => 'boolean',
        'has_pickup' => 'boolean',
        'has_utility' => 'boolean',
        'has_motorcycle' => 'boolean',
        'has_truck' => 'boolean',
        'has_bus' => 'boolean',
        'has_pedestrian' => 'boolean',
        'has_bicycle' => 'boolean',
    ];

    public function category()
    {
        return $this->belongsTo(Category::class);
    }

    public function department()
    {
        return $this->belongsTo(Department::class);
    }

    public function locality()
    {
        return $this->belongsTo(Locality::class);
    }
}
