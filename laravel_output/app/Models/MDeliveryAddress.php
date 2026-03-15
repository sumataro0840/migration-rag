<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class MDeliveryAddress extends Model
{
    use HasFactory;

    protected $table = 'm_delivery_address';

    protected $fillable = [
        'delivery_address_id',
        'customer_id',
        'recipient_name',
        'postal_code',
        'address',
    ];
}
