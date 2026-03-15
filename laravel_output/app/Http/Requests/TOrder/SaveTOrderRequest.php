<?php

namespace App\Http\Requests\TOrder;

use Illuminate\Foundation\Http\FormRequest;

class SaveTOrderRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        $requiredRule = $this->isMethod('post') ? 'required' : 'sometimes';

        return [
            'contact_phone' => [$requiredRule, 'string', 'max:20'],
            'customer_id' => [$requiredRule, 'integer', 'exists:customers,id'],
            'order_date' => [$requiredRule, 'date'],
            'order_id' => [$requiredRule, 'integer', 'exists:orders,id'],
            'shipping_address' => [$requiredRule, 'string', 'max:255'],
        ];
    }
}
