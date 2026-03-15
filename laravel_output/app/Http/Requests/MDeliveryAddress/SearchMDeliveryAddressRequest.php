<?php

namespace App\Http\Requests\MDeliveryAddress;

use Illuminate\Foundation\Http\FormRequest;

class SearchMDeliveryAddressRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'address' => ['nullable', 'string'],
            'customer_id' => ['nullable', 'integer'],
            'delivery_address_id' => ['nullable', 'integer'],
            'postal_code' => ['nullable', 'string'],
            'recipient_name' => ['nullable', 'string'],
            'per_page' => ['nullable', 'integer', 'min:1', 'max:100'],
            'sort' => ['nullable', 'string', 'in:address,customer_id,delivery_address_id,id,postal_code,recipient_name'],
            'direction' => ['nullable', 'in:asc,desc'],
        ];
    }
}
