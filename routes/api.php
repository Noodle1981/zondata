<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\IncidentController;

Route::get('/user', function (Request $request) {
    return $request->user();
})->middleware('auth:sanctum');

Route::get('/incidents', [IncidentController::class, 'index']);
Route::post('/incidents', [IncidentController::class, 'store']);
