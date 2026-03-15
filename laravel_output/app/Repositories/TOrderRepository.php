<?php

namespace App\Repositories;

use App\Models\TOrder;
use Illuminate\Contracts\Pagination\LengthAwarePaginator;

class TOrderRepository
{
    public function search(array $conditions): LengthAwarePaginator
    {
        $query = TOrder::query();

        if (isset($conditions['contact_phone']) && $conditions['contact_phone'] !== '') {
            $query->where('contact_phone', 'like', '%' . $conditions['contact_phone'] . '%');
        }
        if (array_key_exists('customer_id', $conditions) && $conditions['customer_id'] !== null && $conditions['customer_id'] !== '') {
            $query->where('customer_id', $conditions['customer_id']);
        }
        if (isset($conditions['order_date']) && $conditions['order_date'] !== '') {
            $query->whereDate('order_date', $conditions['order_date']);
        }
        if (array_key_exists('order_id', $conditions) && $conditions['order_id'] !== null && $conditions['order_id'] !== '') {
            $query->where('order_id', $conditions['order_id']);
        }
        if (isset($conditions['shipping_address']) && $conditions['shipping_address'] !== '') {
            $query->where('shipping_address', 'like', '%' . $conditions['shipping_address'] . '%');
        }

        $allowedSort = ['contact_phone', 'customer_id', 'id', 'order_date', 'order_id', 'shipping_address'];
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

    public function findById($id): TOrder
    {
        return TOrder::query()->findOrFail($id);
    }

    public function create(array $data): TOrder
    {
        return TOrder::query()->create($data);
    }

    public function update($id, array $data): TOrder
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
