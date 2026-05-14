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
}
