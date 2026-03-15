<?php

namespace App\Http\Controllers;

use App\Models\MDeliveryAddress;
use Illuminate\Http\Request;

class MDeliveryAddressController extends Controller
{
    public function index()
    {
        return MDeliveryAddress::all();
    }

    public function store(Request $request)
    {
        return MDeliveryAddress::create($request->all());
    }

    public function show(int $id)
    {
        return MDeliveryAddress::findOrFail($id);
    }

    public function update(Request $request, int $id)
    {
        $item = MDeliveryAddress::findOrFail($id);
        $item->update($request->all());

        return $item;
    }

    public function destroy(int $id)
    {
        MDeliveryAddress::destroy($id);

        return response()->noContent();
    }
}
