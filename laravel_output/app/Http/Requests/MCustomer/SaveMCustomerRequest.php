<?php

namespace App\Http\Requests\MCustomer;

use Illuminate\Foundation\Http\FormRequest;

class SaveMCustomerRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        $requiredRule = $this->isMethod('post') ? 'required' : 'sometimes';

        return [
            'address' => [$requiredRule, 'string', 'max:255'],
            'customer_id' => [$requiredRule, 'integer', 'exists:customers,id'],
            'customer_name' => [$requiredRule, 'string', 'max:100'],
            'phone_number' => [$requiredRule, 'string', 'max:20'],
            'postal_code' => [$requiredRule, 'string', 'max:8'],
        ];
    }
}
