<?php

namespace App\Repositories;

use App\Models\MDeliveryAddress;
use Illuminate\Contracts\Pagination\LengthAwarePaginator;

class MDeliveryAddressRepository
{
    public function search(array $conditions): LengthAwarePaginator
    {
        $query = MDeliveryAddress::query();

        if (isset($conditions['address']) && $conditions['address'] !== '') {
            $query->where('address', 'like', '%' . $conditions['address'] . '%');
        }
        if (array_key_exists('customer_id', $conditions) && $conditions['customer_id'] !== null && $conditions['customer_id'] !== '') {
            $query->where('customer_id', $conditions['customer_id']);
        }
        if (array_key_exists('delivery_address_id', $conditions) && $conditions['delivery_address_id'] !== null && $conditions['delivery_address_id'] !== '') {
            $query->where('delivery_address_id', $conditions['delivery_address_id']);
        }
        if (isset($conditions['postal_code']) && $conditions['postal_code'] !== '') {
            $query->where('postal_code', 'like', '%' . $conditions['postal_code'] . '%');
        }
        if (isset($conditions['recipient_name']) && $conditions['recipient_name'] !== '') {
            $query->where('recipient_name', 'like', '%' . $conditions['recipient_name'] . '%');
        }

        $allowedSort = ['address', 'customer_id', 'delivery_address_id', 'id', 'postal_code', 'recipient_name'];
        $sort = $conditions['sort'] ?? 'created_at';
        if (!in_array($sort, $allowedSort, true)) {
            $sort = 'created_at';
        }

        $direction = strtolower((string) ($conditions['direction'] ?? 'desc'));
        if (!in_array($direction, ['asc', 'desc'], true)) {
            $direction = 'desc';
        }

        $perPage = (int) ($conditions['per_page'] ?? 15);
        if ($perPage < 1) {
            $perPage = 15;
        }
        if ($perPage > 100) {
            $perPage = 100;
        }

        return $query->orderBy($sort, $direction)->paginate($perPage);
    }

    public function findById($id): MDeliveryAddress
    {
        return MDeliveryAddress::query()->findOrFail($id);
    }

    public function create(array $data): MDeliveryAddress
    {
        return MDeliveryAddress::query()->create($data);
    }

    public function update($id, array $data): MDeliveryAddress
    {
        $model = $this->findById($id);
        $model->fill($data);
        $model->save();

        return $model;
    }

    public function delete($id): bool
    {
        $model = $this->findById($id);
        return (bool) $model->delete();
    }
}
