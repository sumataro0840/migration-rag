"""Route file generator for Laravel 11 (web.php + api.php)."""

from __future__ import annotations

from pathlib import Path

from .schema_converter import TableSchema


class RouteGenerator:
    """Generate Laravel route files.

    - routes/web.php : Blade View と連動した resourceルート
    - routes/api.php : JSON API 用 apiResource ルート（オプション）
    """

    def __init__(self, output_root: str | Path) -> None:
        self.output_root = Path(output_root)
        self.routes_dir  = self.output_root / "routes"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, schemas: list[TableSchema]) -> list[Path]:
        """web.php と api.php を生成してパスのリストを返す。"""
        self.routes_dir.mkdir(parents=True, exist_ok=True)

        web_path = self.routes_dir / "web.php"
        api_path = self.routes_dir / "api.php"

        web_path.write_text(self._render_web(schemas), encoding="utf-8")
        api_path.write_text(self._render_api(schemas), encoding="utf-8")

        return [web_path, api_path]

    # ------------------------------------------------------------------
    # web.php
    # ------------------------------------------------------------------

    def _render_web(self, schemas: list[TableSchema]) -> str:
        imports = "\n".join(
            f"use App\\Http\\Controllers\\{t.model_name}Controller;"
            for t in schemas
        ) or "// No controllers generated"

        routes = "\n".join(
            f"Route::resource('{t.table_name}', {t.model_name}Controller::class);"
            for t in schemas
        ) or "// No routes generated"

        return f"""\
<?php

use Illuminate\\Support\\Facades\\Route;
{imports}

/*
|--------------------------------------------------------------------------
| Web Routes  –  Blade View CRUD
|--------------------------------------------------------------------------
| generate_laravel_app.py によって自動生成されました。
| 各コントローラは resources/views/{{table}}/ 配下のBladeを返します。
*/

Route::get('/', function () {{
    return redirect()->route('dashboard');
}})->name('home');

Route::get('/dashboard', function () {{
    return view('dashboard');
}})->name('dashboard');

{routes}
"""

    # ------------------------------------------------------------------
    # api.php
    # ------------------------------------------------------------------

    def _render_api(self, schemas: list[TableSchema]) -> str:
        imports = "\n".join(
            f"use App\\Http\\Controllers\\{t.model_name}Controller;"
            for t in schemas
        ) or "// No controllers generated"

        routes = "\n".join(
            f"Route::apiResource('{t.table_name}', {t.model_name}Controller::class);"
            for t in schemas
        ) or "// No routes generated"

        return f"""\
<?php

use Illuminate\\Support\\Facades\\Route;
{imports}

/*
|--------------------------------------------------------------------------
| API Routes  –  JSON endpoints
|--------------------------------------------------------------------------
| Web コントローラを共用しています。
| API専用のコントローラに差し替える場合はここを変更してください。
*/

{routes}
"""