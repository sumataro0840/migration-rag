<?php

namespace App\Repositories;

use App\Models\MCustomer;
use Illuminate\Contracts\Pagination\LengthAwarePaginator;

class MCustomerRepository
{
    public function search(array $conditions): LengthAwarePaginator
    {
        $query = MCustomer::query();

        if (isset($conditions['address']) && $conditions['address'] !== '') {
            $query->where('address', 'like', '%' . $conditions['address'] . '%');
        }
        if (array_key_exists('customer_id', $conditions) && $conditions['customer_id'] !== null && $conditions['customer_id'] !== '') {
            $query->where('customer_id', $conditions['customer_id']);
        }
        if (isset($conditions['customer_name']) && $conditions['customer_name'] !== '') {
            $query->where('customer_name', 'like', '%' . $conditions['customer_name'] . '%');
        }
        if (isset($conditions['phone_number']) && $conditions['phone_number'] !== '') {
            $query->where('phone_number', 'like', '%' . $conditions['phone_number'] . '%');
        }
        if (isset($conditions['postal_code']) && $conditions['postal_code'] !== '') {
            $query->where('postal_code', 'like', '%' . $conditions['postal_code'] . '%');
        }

        $allowedSort = ['address', 'customer_id', 'customer_name', 'id', 'phone_number', 'postal_code'];
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

    public function findById($id): MCustomer
    {
        return MCustomer::query()->findOrFail($id);
    }

    public function create(array $data): MCustomer
    {
        return MCustomer::query()->create($data);
    }

    public function update($id, array $data): MCustomer
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
