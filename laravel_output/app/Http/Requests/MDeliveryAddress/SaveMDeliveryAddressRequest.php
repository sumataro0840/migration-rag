<?php

namespace App\Http\Requests\MDeliveryAddress;

use Illuminate\Foundation\Http\FormRequest;

class SaveMDeliveryAddressRequest extends FormRequest
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
            'delivery_address_id' => [$requiredRule, 'integer', 'exists:delivery_address,id'],
            'postal_code' => [$requiredRule, 'string', 'max:8'],
            'recipient_name' => [$requiredRule, 'string', 'max:100'],
        ];
    }
}
