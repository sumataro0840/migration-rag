"""Controller file generator."""

from __future__ import annotations

from pathlib import Path

from .schema_converter import TableSchema


class ControllerGenerator:
    """Generate API controllers with basic CRUD endpoints."""

    def __init__(self, output_root: str | Path) -> None:
        self.output_root = Path(output_root)
        self.controller_dir = self.output_root / "app" / "Http" / "Controllers"

    def generate(self, schemas: list[TableSchema]) -> list[Path]:
        self.controller_dir.mkdir(parents=True, exist_ok=True)

        generated_paths: list[Path] = []
        for table in schemas:
            controller_name = f"{table.model_name}Controller"
            file_path = self.controller_dir / f"{controller_name}.php"
            file_path.write_text(
                self._render_controller(model_name=table.model_name, controller_name=controller_name),
                encoding="utf-8",
            )
            generated_paths.append(file_path)

        return generated_paths

    @staticmethod
    def _render_controller(model_name: str, controller_name: str) -> str:
        return f"""<?php

namespace App\\Http\\Controllers;

use App\\Models\\{model_name};
use Illuminate\\Http\\Request;

class {controller_name} extends Controller
{{
    public function index()
    {{
        return {model_name}::all();
    }}

    public function store(Request $request)
    {{
        return {model_name}::create($request->all());
    }}

    public function show(int $id)
    {{
        return {model_name}::findOrFail($id);
    }}

    public function update(Request $request, int $id)
    {{
        $item = {model_name}::findOrFail($id);
        $item->update($request->all());

        return $item;
    }}

    public function destroy(int $id)
    {{
        {model_name}::destroy($id);

        return response()->noContent();
    }}
}}
"""
