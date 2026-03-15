<?php

namespace App\Http\Requests\TOrder;

use Illuminate\Foundation\Http\FormRequest;

class SearchTOrderRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'contact_phone' => ['nullable', 'string'],
            'customer_id' => ['nullable', 'integer'],
            'order_date' => ['nullable', 'date'],
            'order_id' => ['nullable', 'integer'],
            'shipping_address' => ['nullable', 'string'],
            'per_page' => ['nullable', 'integer', 'min:1', 'max:100'],
            'sort' => ['nullable', 'string', 'in:contact_phone,customer_id,id,order_date,order_id,shipping_address'],
            'direction' => ['nullable', 'in:asc,desc'],
        ];
    }
}
