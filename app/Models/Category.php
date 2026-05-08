<?php

namespace App\Models;

use Backpack\CRUD\app\Models\Traits\CrudTrait;
use Illuminate\Database\Eloquent\Model;

class Category extends Model
{
    use CrudTrait;
    protected $fillable = ['name', 'slug'];

    public function incidents()
    {
        return $this->hasMany(Incident::class);
    }
}
