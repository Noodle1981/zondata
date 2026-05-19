<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Locality extends Model
{
    protected $fillable = ['department_id', 'name', 'lat', 'lon'];

    public function department()
    {
        return $this->belongsTo(Department::class);
    }
}
