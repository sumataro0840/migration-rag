<?php

namespace App\Services;

use App\Models\MDeliveryAddress;
use App\Repositories\MDeliveryAddressRepository;
use Illuminate\Contracts\Pagination\LengthAwarePaginator;

class MDeliveryAddressService
{
    public function __construct(private readonly MDeliveryAddressRepository $repository)
    {
    }

    public function search(array $conditions): LengthAwarePaginator
    {
        return $this->repository->search($conditions);
    }

    public function findById($id): MDeliveryAddress
    {
        return $this->repository->findById($id);
    }

    public function create(array $data): MDeliveryAddress
    {
        return $this->repository->create($data);
    }

    public function update($id, array $data): MDeliveryAddress
    {
        return $this->repository->update($id, $data);
    }

    public function delete($id): bool
    {
        return $this->repository->delete($id);
    }
}
