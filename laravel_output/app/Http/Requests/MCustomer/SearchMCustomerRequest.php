<?php

namespace App\Http\Requests\MCustomer;

use Illuminate\Foundation\Http\FormRequest;

class SearchMCustomerRequest extends FormRequest
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
            'customer_name' => ['nullable', 'string'],
            'phone_number' => ['nullable', 'string'],
            'postal_code' => ['nullable', 'string'],
            'per_page' => ['nullable', 'integer', 'min:1', 'max:100'],
            'sort' => ['nullable', 'string', 'in:address,customer_id,customer_name,id,phone_number,postal_code'],
            'direction' => ['nullable', 'in:asc,desc'],
        ];
    }
}
