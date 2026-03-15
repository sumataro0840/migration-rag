<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class MCustomer extends Model
{
    use HasFactory;

    protected $table = 'm_customers';

    protected $fillable = [
        'customer_id',
        'customer_name',
        'postal_code',
        'address',
        'phone_number',
    ];
}
