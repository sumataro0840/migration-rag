"""Route file generator."""

from __future__ import annotations

from pathlib import Path

from .schema_converter import TableSchema


class RouteGenerator:
    """Generate Laravel API routes file."""

    def __init__(self, output_root: str | Path) -> None:
        self.output_root = Path(output_root)
        self.route_file = self.output_root / "routes" / "api.php"

    def generate(self, schemas: list[TableSchema]) -> Path:
        self.route_file.parent.mkdir(parents=True, exist_ok=True)
        self.route_file.write_text(self._render_routes(schemas), encoding="utf-8")
        return self.route_file

    def _render_routes(self, schemas: list[TableSchema]) -> str:
        controller_imports = "\n".join(
            f"use App\\Http\\Controllers\\{table.model_name}Controller;" for table in schemas
        )
        route_lines = "\n".join(
            f"Route::apiResource('{table.table_name}', {table.model_name}Controller::class);"
            for table in schemas
        )

        if not controller_imports:
            controller_imports = "// No controllers generated"
        if not route_lines:
            route_lines = "// No routes generated"

        return f"""<?php

use Illuminate\\Support\\Facades\\Route;
{controller_imports}

{route_lines}
"""
