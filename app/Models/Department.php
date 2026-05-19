<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Department extends Model
{
    protected $fillable = ['province_id', 'name', 'lat', 'lon'];

    public function province()
    {
        return $this->belongsTo(Province::class);
    }

    public function localities()
    {
        return $this->hasMany(Locality::class);
    }
}
