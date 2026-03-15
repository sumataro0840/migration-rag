<?php

namespace App\Services;

use App\Models\TOrder;
use App\Repositories\TOrderRepository;
use Illuminate\Contracts\Pagination\LengthAwarePaginator;

class TOrderService
{
    public function __construct(private readonly TOrderRepository $repository)
    {
    }

    public function search(array $conditions): LengthAwarePaginator
    {
        return $this->repository->search($conditions);
    }

    public function findById($id): TOrder
    {
        return $this->repository->findById($id);
    }

    public function create(array $data): TOrder
    {
        return $this->repository->create($data);
    }

    public function update($id, array $data): TOrder
    {
        return $this->repository->update($id, $data);
    }

    public function delete($id): bool
    {
        return $this->repository->delete($id);
    }
}
