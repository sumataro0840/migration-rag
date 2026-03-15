"""Web Controller file generator for Laravel 11 (resource CRUD + Blade views)."""

from __future__ import annotations

from pathlib import Path

from .schema_converter import ColumnSchema, TableSchema

# フォームに出さないシステムカラム（バリデーションでも除外）
_SYSTEM_COLUMNS = {"created_at", "updated_at", "deleted_at"}


class ControllerGenerator:
    """Generate Web resource controllers that work with Blade views."""

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
                self._render_controller(table),
                encoding="utf-8",
            )
            generated_paths.append(file_path)

        return generated_paths

    # ------------------------------------------------------------------
    # ヘルパー
    # ------------------------------------------------------------------

    @staticmethod
    def _form_columns(table: TableSchema) -> list[ColumnSchema]:
        """フォーム送信・バリデーション対象カラム（PK・システムカラム除外）。"""
        return [
            col for col in table.columns
            if not col.primary and col.name not in _SYSTEM_COLUMNS
        ]

    @staticmethod
    def _fk_columns(table: TableSchema) -> list[ColumnSchema]:
        """_id で終わる外部キーカラム一覧（select 用 Options が必要）。"""
        return [
            col for col in table.columns
            if col.name.endswith("_id") and not col.primary
        ]

    @staticmethod
    def _options_var(col: ColumnSchema) -> str:
        """customer_id -> customerOptions"""
        return col.name[:-3] + "Options"

    @staticmethod
    def _blade_var(table: TableSchema) -> str:
        """MCustomer -> mCustomer"""
        n = table.model_name
        return n[0].lower() + n[1:]

    @staticmethod
    def _route_prefix(table: TableSchema) -> str:
        return table.table_name

    # ------------------------------------------------------------------
    # バリデーションルール生成
    # ------------------------------------------------------------------

    @staticmethod
    def _validation_rule(col: ColumnSchema) -> str:
        """カラム1本分のバリデーションルール文字列を返す。"""
        rules: list[str] = []

        if col.nullable:
            rules.append("'nullable'")
        else:
            rules.append("'required'")

        dt = col.data_type.lower()
        if col.name.endswith("_id"):
            rules.append("'integer'")
        elif dt in {"integer", "bigint", "smallint", "tinyint", "int"}:
            rules.append("'integer'")
        elif dt in {"decimal", "numeric", "float", "double"}:
            rules.append("'numeric'")
        elif dt in {"boolean", "bool"}:
            rules.append("'boolean'")
        elif dt in {"date"}:
            rules.append("'date'")
        elif dt in {"datetime", "timestamp"}:
            rules.append("'date'")
        else:
            rules.append("'string'")
            if col.length:
                rules.append(f"'max:{col.length}'")

        return f"            '{col.name}' => [{', '.join(rules)}],"

    # ------------------------------------------------------------------
    # コントローラレンダリング
    # ------------------------------------------------------------------

    @staticmethod
    def _pk_column(table: TableSchema) -> str:
        """PKカラム名を返す。見つからなければ 'id'。"""
        for col in table.columns:
            if col.primary:
                return col.name
        return "id"

    def _render_controller(self, table: TableSchema) -> str:
        name       = table.model_name
        controller = f"{name}Controller"
        route      = self._route_prefix(table)
        var        = self._blade_var(table)
        pk         = self._pk_column(table)
        form_cols  = self._form_columns(table)
        fk_cols    = self._fk_columns(table)

        fk_model_imports   = self._render_fk_imports(fk_cols, table)
        rules_lines        = "\n".join(self._validation_rule(c) for c in form_cols)
        if not rules_lines:
            rules_lines    = "            // No writable columns"

        # create: compact('opt1', 'opt2') / edit: compact('var', 'opt1', 'opt2')
        create_compact     = self._render_create_compact(fk_cols)
        edit_compact       = self._render_edit_compact(var, fk_cols)
        options_fetch      = self._render_options_fetch(fk_cols, "        ")

        return f"""\
<?php

namespace App\\Http\\Controllers;

use App\\Models\\{name};
use Illuminate\\Http\\Request;
use Illuminate\\Http\\RedirectResponse;
use Illuminate\\View\\View;
{fk_model_imports}
class {controller} extends Controller
{{
    /**
     * 一覧表示
     */
    public function index(): View
    {{
        $items = {name}::orderByDesc('{pk}')->paginate(15);

        return view('{route}.index', compact('items'));
    }}

    /**
     * 新規作成フォーム
     */
    public function create(): View
    {{
{options_fetch}
        return view('{route}.create'{create_compact});
    }}

    /**
     * 新規作成処理
     */
    public function store(Request $request): RedirectResponse
    {{
        $validated = $request->validate([
{rules_lines}
        ]);

        {name}::create($validated);

        return redirect()->route('{route}.index')
            ->with('success', '登録しました。');
    }}

    /**
     * 詳細表示
     */
    public function show({name} ${var}): View
    {{
        return view('{route}.show', compact('{var}'));
    }}

    /**
     * 編集フォーム
     */
    public function edit({name} ${var}): View
    {{
{options_fetch}
        return view('{route}.edit', {edit_compact});
    }}

    /**
     * 更新処理
     */
    public function update(Request $request, {name} ${var}): RedirectResponse
    {{
        $validated = $request->validate([
{rules_lines}
        ]);

        ${var}->update($validated);

        return redirect()->route('{route}.index')
            ->with('success', '更新しました。');
    }}

    /**
     * 削除処理
     */
    public function destroy({name} ${var}): RedirectResponse
    {{
        ${var}->delete();

        return redirect()->route('{route}.index')
            ->with('success', '削除しました。');
    }}
}}
"""

    def _render_fk_imports(self, fk_cols: list[ColumnSchema], table: TableSchema) -> str:
        """FK先モデルの use 文を生成する（重複排除）。"""
        if not fk_cols:
            return ""

        seen: set[str] = {table.model_name}
        lines: list[str] = []
        for col in fk_cols:
            model = "".join(p.capitalize() for p in col.name[:-3].split("_"))
            if model and model not in seen:
                seen.add(model)
                lines.append(f"use App\\Models\\{model};")

        if not lines:
            return ""
        return "\n".join(lines) + "\n"

    def _render_options_fetch(self, fk_cols: list[ColumnSchema], indent: str) -> str:
        """FK select 用 Options の取得コードを生成する。"""
        if not fk_cols:
            return ""

        lines: list[str] = []
        for col in fk_cols:
            model       = "".join(p.capitalize() for p in col.name[:-3].split("_"))
            options_var = self._options_var(col)
            lines.append(
                f"{indent}// TODO: {model} の表示カラム（例: 'name'）を適宜変更してください\n"
                f"{indent}${options_var} = \\App\\Models\\{model}::orderBy('id')"
                f"->pluck('id', 'id');"
            )

        return "\n".join(lines) + "\n"

    def _render_create_compact(self, fk_cols: list[ColumnSchema]) -> str:
        """create() 用 compact() 引数文字列。FK Optionsのみ。"""
        if not fk_cols:
            return ""
        keys = ", ".join(f"'{self._options_var(col)}'" for col in fk_cols)
        return f", compact({keys})"

    def _render_edit_compact(self, var: str, fk_cols: list[ColumnSchema]) -> str:
        """edit() 用 compact() 引数文字列。モデル変数 + FK Options。"""
        keys = [f"'{var}'"] + [f"'{self._options_var(col)}'" for col in fk_cols]
        return f"compact({', '.join(keys)})"