<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\MCustomerController;
use App\Http\Controllers\TOrderController;
use App\Http\Controllers\MDeliveryAddressController;

Route::apiResource('m_customers', MCustomerController::class);
Route::apiResource('t_orders', TOrderController::class);
Route::apiResource('m_delivery_address', MDeliveryAddressController::class);
