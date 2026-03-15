<?php

namespace App\Http\Controllers;

use App\Models\MCustomer;
use Illuminate\Http\Request;

class MCustomerController extends Controller
{
    public function index()
    {
        return MCustomer::all();
    }

    public function store(Request $request)
    {
        return MCustomer::create($request->all());
    }

    public function show(int $id)
    {
        return MCustomer::findOrFail($id);
    }

    public function update(Request $request, int $id)
    {
        $item = MCustomer::findOrFail($id);
        $item->update($request->all());

        return $item;
    }

    public function destroy(int $id)
    {
        MCustomer::destroy($id);

        return response()->noContent();
    }
}
