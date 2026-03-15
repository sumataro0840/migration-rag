<?php

namespace App\Http\Controllers;

use App\Models\TOrder;
use Illuminate\Http\Request;

class TOrderController extends Controller
{
    public function index()
    {
        return TOrder::all();
    }

    public function store(Request $request)
    {
        return TOrder::create($request->all());
    }

    public function show(int $id)
    {
        return TOrder::findOrFail($id);
    }

    public function update(Request $request, int $id)
    {
        $item = TOrder::findOrFail($id);
        $item->update($request->all());

        return $item;
    }

    public function destroy(int $id)
    {
        TOrder::destroy($id);

        return response()->noContent();
    }
}
