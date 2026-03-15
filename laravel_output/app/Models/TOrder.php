<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class TOrder extends Model
{
    use HasFactory;

    protected $table = 't_orders';

    protected $fillable = [
        'order_id',
        'customer_id',
        'order_date',
        'shipping_address',
        'contact_phone',
    ];
}
