<?php

declare(strict_types=1);

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use Claviron\Bench\Workload;

Route::get('/bench/plain', static fn () => response(Workload::PLAIN, 200, [
    'Content-Type' => 'text/plain',
]));

Route::get('/bench/json', static fn () => response()->json(Workload::json()));

Route::post('/bench/echo', static fn (Request $request) => response($request->getContent(), 200, [
    'Content-Type' => 'application/octet-stream',
]));
