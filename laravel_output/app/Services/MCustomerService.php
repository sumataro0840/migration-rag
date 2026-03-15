<?php

namespace App\Services;

use App\Models\MCustomer;
use App\Repositories\MCustomerRepository;
use Illuminate\Contracts\Pagination\LengthAwarePaginator;

class MCustomerService
{
    public function __construct(private readonly MCustomerRepository $repository)
    {
    }

    public function search(array $conditions): LengthAwarePaginator
    {
        return $this->repository->search($conditions);
    }

    public function findById($id): MCustomer
    {
        return $this->repository->findById($id);
    }

    public function create(array $data): MCustomer
    {
        return $this->repository->create($data);
    }

    public function update($id, array $data): MCustomer
    {
        return $this->repository->update($id, $data);
    }

    public function delete($id): bool
    {
        return $this->repository->delete($id);
    }
}
