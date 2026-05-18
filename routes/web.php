<?php

use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return view('welcome');
});

Route::get('/dashboard_public', function () {
    return view('welcome');
});

Route::get('/dashboard_públic', function () {
    return view('welcome');
});

Route::get('/dashboard_premium', function () {
    return view('welcome');
});
