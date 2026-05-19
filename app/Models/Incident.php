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
        'is_fatal',
        'event_date',
        'status',
        'locality_id',
        'department_id',
        'province_id',
    ];

    protected $casts = [
        'event_date' => 'datetime',
        'is_approximate' => 'boolean',
        'is_fatal' => 'boolean',
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
