"""Blade View file generator for Laravel 11.

生成するファイル:
  resources/views/layouts/app.blade.php          共通レイアウト (Tailwind CDN)
  resources/views/dashboard.blade.php            トップ: テーブル一覧リンク
  resources/views/{table}/index.blade.php
  resources/views/{table}/create.blade.php
  resources/views/{table}/edit.blade.php
  resources/views/{table}/show.blade.php
  resources/views/{table}/partials/form.blade.php
"""

from __future__ import annotations

from pathlib import Path

from .schema_converter import ColumnSchema, TableSchema

_SYSTEM_COLUMNS = {"created_at", "updated_at", "deleted_at"}

_TYPE_MAP: dict[str, str] = {
    "integer":    "number",
    "bigint":     "number",
    "smallint":   "number",
    "tinyint":    "number",
    "int":        "number",
    "float":      "number",
    "double":     "number",
    "decimal":    "number",
    "numeric":    "number",
    "boolean":    "checkbox",
    "bool":       "checkbox",
    "date":       "date",
    "datetime":   "datetime-local",
    "timestamp":  "datetime-local",
    "text":       "textarea",
    "mediumtext": "textarea",
    "longtext":   "textarea",
}

# テーブルごとにアクセントカラーを変える
_ACCENT_COLORS = [
    ("blue",    "bg-blue-600",    "hover:bg-blue-700",    "text-blue-600",    "border-blue-500"),
    ("violet",  "bg-violet-600",  "hover:bg-violet-700",  "text-violet-600",  "border-violet-500"),
    ("emerald", "bg-emerald-600", "hover:bg-emerald-700", "text-emerald-600", "border-emerald-500"),
    ("rose",    "bg-rose-600",    "hover:bg-rose-700",    "text-rose-600",    "border-rose-500"),
    ("amber",   "bg-amber-500",   "hover:bg-amber-600",   "text-amber-600",   "border-amber-500"),
]


def _accent(index: int) -> dict[str, str]:
    name, bg, bg_hover, text, border = _ACCENT_COLORS[index % len(_ACCENT_COLORS)]
    return {"name": name, "bg": bg, "bg_hover": bg_hover, "text": text, "border": border}


# 共通フォームパーツの CSS クラス
_INPUT_CLASS = (
    "mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm "
    "focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
)
_LABEL_CLASS = "block text-sm font-medium text-gray-700"
_ERROR_CLASS = "mt-1 text-red-500 text-xs"


class ViewGenerator:
    """Generate Blade view files from normalized TableSchema objects."""

    def __init__(self, output_root: str | Path) -> None:
        self.output_root = Path(output_root)

    def generate(self, schemas: list[TableSchema]) -> list[Path]:
        """全ファイルを生成してパスのリストを返す。"""
        views_dir = self.output_root / "resources" / "views"
        generated: list[Path] = []

        # 共通レイアウト
        layout_dir = views_dir / "layouts"
        layout_dir.mkdir(parents=True, exist_ok=True)
        layout_path = layout_dir / "app.blade.php"
        layout_path.write_text(self._render_layout(schemas), encoding="utf-8")
        generated.append(layout_path)

        # ダッシュボード（トップページ）
        views_dir.mkdir(parents=True, exist_ok=True)
        dashboard_path = views_dir / "dashboard.blade.php"
        dashboard_path.write_text(self._render_dashboard(schemas), encoding="utf-8")
        generated.append(dashboard_path)

        # テーブルごとの CRUD ビュー
        for i, table in enumerate(schemas):
            generated.extend(self._generate_for_table(table, _accent(i)))

        return generated

    # ------------------------------------------------------------------
    # 共通レイアウト
    # ------------------------------------------------------------------

    def _render_layout(self, schemas: list[TableSchema]) -> str:
        nav_links = "\n".join(
            f"                <a href=\"{{{{ route('{t.table_name}.index') }}}}\" "
            f"class=\"text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium\""
            f">{t.table_name}</a>"
            for t in schemas
        )

        return (
            "<!DOCTYPE html>\n"
            "<html lang=\"ja\">\n"
            "<head>\n"
            "    <meta charset=\"UTF-8\">\n"
            "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
            "    <meta name=\"csrf-token\" content=\"{{ csrf_token() }}\">\n"
            "    <title>@yield('title', 'Laravel App')</title>\n"
            "    {{-- Tailwind CSS CDN --}}\n"
            "    <script src=\"https://cdn.tailwindcss.com\"></script>\n"
            "</head>\n"
            "<body class=\"bg-gray-100 min-h-screen\">\n"
            "\n"
            "{{-- ナビゲーションバー --}}\n"
            "<nav class=\"bg-gray-800 shadow\">\n"
            "    <div class=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8\">\n"
            "        <div class=\"flex items-center justify-between h-16\">\n"
            "            <div class=\"flex items-center\">\n"
            "                <a href=\"{{ route('dashboard') }}\" class=\"text-white font-bold text-lg mr-8\">\n"
            "                    &#128193; Laravel App\n"
            "                </a>\n"
            "                <div class=\"flex space-x-1\">\n"
            f"{nav_links}\n"
            "                </div>\n"
            "            </div>\n"
            "        </div>\n"
            "    </div>\n"
            "</nav>\n"
            "\n"
            "{{-- フラッシュメッセージ --}}\n"
            "@if(session('success'))\n"
            "<div class=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4\">\n"
            "    <div class=\"flex items-center gap-2 bg-green-50 border border-green-400 text-green-800 px-4 py-3 rounded-lg\">\n"
            "        <span>&#9989;</span>\n"
            "        <span>{{ session('success') }}</span>\n"
            "    </div>\n"
            "</div>\n"
            "@endif\n"
            "\n"
            "@if(session('error'))\n"
            "<div class=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4\">\n"
            "    <div class=\"flex items-center gap-2 bg-red-50 border border-red-400 text-red-800 px-4 py-3 rounded-lg\">\n"
            "        <span>&#10060;</span>\n"
            "        <span>{{ session('error') }}</span>\n"
            "    </div>\n"
            "</div>\n"
            "@endif\n"
            "\n"
            "{{-- メインコンテンツ --}}\n"
            "<main class=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8\">\n"
            "    @yield('content')\n"
            "</main>\n"
            "\n"
            "</body>\n"
            "</html>\n"
        )

    # ------------------------------------------------------------------
    # ダッシュボード
    # ------------------------------------------------------------------

    def _render_dashboard(self, schemas: list[TableSchema]) -> str:
        cards = "\n".join(
            self._render_dashboard_card(t, _accent(i))
            for i, t in enumerate(schemas)
        )
        return (
            "@extends('layouts.app')\n\n"
            "@section('title', 'ダッシュボード')\n\n"
            "@section('content')\n"
            "<div class=\"mb-8\">\n"
            "    <h1 class=\"text-3xl font-bold text-gray-900\">ダッシュボード</h1>\n"
            "    <p class=\"mt-1 text-gray-500\">管理するテーブルを選択してください</p>\n"
            "</div>\n\n"
            "<div class=\"grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6\">\n"
            f"{cards}\n"
            "</div>\n"
            "@endsection\n"
        )

    @staticmethod
    def _render_dashboard_card(table: TableSchema, accent: dict[str, str]) -> str:
        route     = table.table_name
        col_count = len(table.columns)
        return (
            f"    <a href=\"{{{{ route('{route}.index') }}}}\" "
            f"class=\"block bg-white rounded-xl shadow hover:shadow-md transition-shadow border-l-4 {accent['border']} p-6\">\n"
            f"        <div class=\"flex items-center justify-between\">\n"
            f"            <div>\n"
            f"                <p class=\"text-xs font-semibold {accent['text']} uppercase tracking-wide\">テーブル</p>\n"
            f"                <h2 class=\"mt-1 text-xl font-bold text-gray-900\">{table.table_name}</h2>\n"
            f"                <p class=\"mt-1 text-sm text-gray-500\">{col_count} カラム</p>\n"
            f"            </div>\n"
            f"            <div class=\"text-4xl opacity-20\">&#128451;</div>\n"
            f"        </div>\n"
            f"        <div class=\"mt-4 text-sm {accent['text']} font-medium\">一覧を見る &#8594;</div>\n"
            f"    </a>"
        )

    # ------------------------------------------------------------------
    # テーブル単位の生成
    # ------------------------------------------------------------------

    def _generate_for_table(self, table: TableSchema, accent: dict[str, str]) -> list[Path]:
        view_dir    = self.output_root / "resources" / "views" / table.table_name
        partial_dir = view_dir / "partials"
        view_dir.mkdir(parents=True, exist_ok=True)
        partial_dir.mkdir(parents=True, exist_ok=True)

        files = {
            view_dir / "index.blade.php":   self._render_index(table, accent),
            view_dir / "create.blade.php":  self._render_create(table, accent),
            view_dir / "edit.blade.php":    self._render_edit(table, accent),
            view_dir / "show.blade.php":    self._render_show(table, accent),
            partial_dir / "form.blade.php": self._render_form(table),
        }

        paths: list[Path] = []
        for path, content in files.items():
            path.write_text(content, encoding="utf-8")
            paths.append(path)
        return paths

    # ------------------------------------------------------------------
    # ヘルパー
    # ------------------------------------------------------------------

    @staticmethod
    def _label(column: ColumnSchema) -> str:
        if column.logical_name:
            return column.logical_name
        return column.name.replace("_", " ").title()

    @staticmethod
    def _form_columns(table: TableSchema) -> list[ColumnSchema]:
        return [
            col for col in table.columns
            if not col.primary and col.name not in _SYSTEM_COLUMNS
        ]

    @staticmethod
    def _display_columns(table: TableSchema) -> list[ColumnSchema]:
        skip_types = {"text", "mediumtext", "longtext"}
        return [col for col in table.columns if col.data_type.lower() not in skip_types]

    @staticmethod
    def _var(table: TableSchema) -> str:
        n = table.model_name
        return n[0].lower() + n[1:]

    @staticmethod
    def _route_prefix(table: TableSchema) -> str:
        return table.table_name

    # ------------------------------------------------------------------
    # フォームフィールド
    # ------------------------------------------------------------------

    def _render_field(self, col: ColumnSchema, table: TableSchema) -> str:
        label    = self._label(col)
        name     = col.name
        var      = self._var(table)
        required = "" if col.nullable else " required"
        dt       = col.data_type.lower()

        if name.endswith("_id"):
            return self._field_select_fk(name, label, var, required)
        if dt == "enum":
            return self._field_select_enum(name, label, var, required)
        if dt in {"boolean", "bool"}:
            return self._field_checkbox(name, label, var)
        if dt in {"text", "mediumtext", "longtext"}:
            return self._field_textarea(name, label, var, required)
        return self._field_input(name, label, var, _TYPE_MAP.get(dt, "text"), required)

    def _field_input(self, name: str, label: str, var: str, input_type: str, required: str) -> str:
        return (
            f"    <div>\n"
            f"        <label class=\"{_LABEL_CLASS}\">{label}</label>\n"
            f"        <input\n"
            f"            type=\"{input_type}\"\n"
            f"            name=\"{name}\"\n"
            f"            value=\"{{{{ old('{name}', ${var}->{name} ?? '') }}}}\"\n"
            f"            class=\"{_INPUT_CLASS}\"{required}\n"
            f"        >\n"
            f"        @error('{name}')\n"
            f"            <p class=\"{_ERROR_CLASS}\">{{{{ $message }}}}</p>\n"
            f"        @enderror\n"
            f"    </div>"
        )

    def _field_textarea(self, name: str, label: str, var: str, required: str) -> str:
        return (
            f"    <div>\n"
            f"        <label class=\"{_LABEL_CLASS}\">{label}</label>\n"
            f"        <textarea\n"
            f"            name=\"{name}\"\n"
            f"            rows=\"4\"\n"
            f"            class=\"{_INPUT_CLASS}\"{required}\n"
            f"        >{{{{ old('{name}', ${var}->{name} ?? '') }}}}</textarea>\n"
            f"        @error('{name}')\n"
            f"            <p class=\"{_ERROR_CLASS}\">{{{{ $message }}}}</p>\n"
            f"        @enderror\n"
            f"    </div>"
        )

    def _field_checkbox(self, name: str, label: str, var: str) -> str:
        return (
            f"    <div class=\"flex items-center gap-3\">\n"
            f"        <input\n"
            f"            type=\"checkbox\"\n"
            f"            name=\"{name}\"\n"
            f"            value=\"1\"\n"
            f"            {{{{ old('{name}', ${var}->{name} ?? false) ? 'checked' : '' }}}}\n"
            f"            class=\"h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500\"\n"
            f"        >\n"
            f"        <label class=\"{_LABEL_CLASS}\">{label}</label>\n"
            f"        @error('{name}')\n"
            f"            <p class=\"{_ERROR_CLASS}\">{{{{ $message }}}}</p>\n"
            f"        @enderror\n"
            f"    </div>"
        )

    def _field_select_fk(self, name: str, label: str, var: str, required: str) -> str:
        options_var = name[:-3] + "Options"
        return (
            f"    <div>\n"
            f"        <label class=\"{_LABEL_CLASS}\">{label}</label>\n"
            f"        <select\n"
            f"            name=\"{name}\"\n"
            f"            class=\"{_INPUT_CLASS}\"{required}\n"
            f"        >\n"
            f"            <option value=\"\">-- 選択してください --</option>\n"
            f"            @foreach(${options_var} as $optId => $optLabel)\n"
            f"                <option value=\"{{{{ $optId }}}}\" {{{{ old('{name}', ${var}->{name} ?? '') == $optId ? 'selected' : '' }}}}>{{{{ $optLabel }}}}</option>\n"
            f"            @endforeach\n"
            f"        </select>\n"
            f"        @error('{name}')\n"
            f"            <p class=\"{_ERROR_CLASS}\">{{{{ $message }}}}</p>\n"
            f"        @enderror\n"
            f"    </div>"
        )

    def _field_select_enum(self, name: str, label: str, var: str, required: str) -> str:
        options_var = name + "Options"
        return (
            f"    <div>\n"
            f"        <label class=\"{_LABEL_CLASS}\">{label}</label>\n"
            f"        <select\n"
            f"            name=\"{name}\"\n"
            f"            class=\"{_INPUT_CLASS}\"{required}\n"
            f"        >\n"
            f"            <option value=\"\">-- 選択してください --</option>\n"
            f"            @foreach(${options_var} as $value => $display)\n"
            f"                <option value=\"{{{{ $value }}}}\" {{{{ old('{name}', ${var}->{name} ?? '') == $value ? 'selected' : '' }}}}>{{{{ $display }}}}</option>\n"
            f"            @endforeach\n"
            f"        </select>\n"
            f"        @error('{name}')\n"
            f"            <p class=\"{_ERROR_CLASS}\">{{{{ $message }}}}</p>\n"
            f"        @enderror\n"
            f"    </div>"
        )

    # ------------------------------------------------------------------
    # form.blade.php（パーシャル）
    # ------------------------------------------------------------------

    def _render_form(self, table: TableSchema) -> str:
        form_cols   = self._form_columns(table)
        fields_html = "\n\n".join(self._render_field(col, table) for col in form_cols)
        return (
            f"{{{{-- {table.table_name} partials/form.blade.php --}}}}\n"
            f"{{{{-- このファイルは create / edit から @include されます --}}}}\n\n"
            f"{fields_html}\n"
        )

    # ------------------------------------------------------------------
    # index.blade.php
    # ------------------------------------------------------------------

    def _render_index(self, table: TableSchema, accent: dict[str, str]) -> str:
        route = self._route_prefix(table)
        disp  = self._display_columns(table)

        th_rows = "\n".join(
            f"                    <th class=\"px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider\">"
            f"{self._label(c)}</th>"
            for c in disp
        )
        th_rows += "\n                    <th class=\"px-6 py-3\"></th>"

        td_rows = "\n".join(
            f"                    <td class=\"px-6 py-4 whitespace-nowrap text-sm text-gray-900\">"
            f"{{{{ $item->{c.name} }}}}</td>"
            for c in disp
        )
        td_rows += (
            f"\n                    <td class=\"px-6 py-4 whitespace-nowrap text-sm font-medium space-x-3\">\n"
            f"                        <a href=\"{{{{ route('{route}.show', $item) }}}}\" class=\"text-blue-600 hover:text-blue-900\">詳細</a>\n"
            f"                        <a href=\"{{{{ route('{route}.edit', $item) }}}}\" class=\"text-yellow-600 hover:text-yellow-900\">編集</a>\n"
            f"                        <form method=\"POST\" action=\"{{{{ route('{route}.destroy', $item) }}}}\" class=\"inline\"\n"
            f"                              onsubmit=\"return confirm('削除しますか？')\">\n"
            f"                            @csrf\n"
            f"                            @method('DELETE')\n"
            f"                            <button type=\"submit\" class=\"text-red-600 hover:text-red-900\">削除</button>\n"
            f"                        </form>\n"
            f"                    </td>"
        )

        return (
            "@extends('layouts.app')\n\n"
            f"@section('title', '{table.table_name} 一覧')\n\n"
            "@section('content')\n"
            "<div class=\"mb-6 flex items-center justify-between\">\n"
            "    <div>\n"
            f"        <h1 class=\"text-2xl font-bold text-gray-900\">{table.table_name}</h1>\n"
            "        <p class=\"mt-1 text-sm text-gray-500\">登録されているデータの一覧</p>\n"
            "    </div>\n"
            f"    <a href=\"{{{{ route('{route}.create') }}}}\"\n"
            f"       class=\"inline-flex items-center gap-2 px-4 py-2 {accent['bg']} {accent['bg_hover']} text-white text-sm font-medium rounded-lg shadow transition-colors\">\n"
            "        &#xff0b; 新規作成\n"
            "    </a>\n"
            "</div>\n\n"
            "<div class=\"bg-white rounded-xl shadow overflow-hidden\">\n"
            "    <table class=\"min-w-full divide-y divide-gray-200\">\n"
            "        <thead class=\"bg-gray-50\">\n"
            "            <tr>\n"
            f"{th_rows}\n"
            "            </tr>\n"
            "        </thead>\n"
            "        <tbody class=\"bg-white divide-y divide-gray-200\">\n"
            "            @forelse($items as $item)\n"
            "            <tr class=\"hover:bg-gray-50 transition-colors\">\n"
            f"{td_rows}\n"
            "            </tr>\n"
            "            @empty\n"
            "            <tr>\n"
            f"                <td colspan=\"{len(disp) + 1}\" class=\"px-6 py-12 text-center text-gray-400\">\n"
            "                    <div class=\"text-4xl mb-2\">&#128253;</div>\n"
            "                    <div class=\"text-sm\">データがありません</div>\n"
            "                </td>\n"
            "            </tr>\n"
            "            @endforelse\n"
            "        </tbody>\n"
            "    </table>\n"
            "</div>\n\n"
            "<div class=\"mt-4\">\n"
            "    {{ $items->links() }}\n"
            "</div>\n"
            "@endsection\n"
        )

    # ------------------------------------------------------------------
    # create.blade.php
    # ------------------------------------------------------------------

    def _render_create(self, table: TableSchema, accent: dict[str, str]) -> str:
        route = self._route_prefix(table)
        return (
            "@extends('layouts.app')\n\n"
            f"@section('title', '{table.table_name} 新規作成')\n\n"
            "@section('content')\n"
            "<div class=\"mb-6 flex items-center gap-3\">\n"
            f"    <a href=\"{{{{ route('{route}.index') }}}}\" class=\"text-gray-400 hover:text-gray-600 text-sm\">&#8592; 一覧へ戻る</a>\n"
            "    <span class=\"text-gray-300\">/</span>\n"
            "    <h1 class=\"text-2xl font-bold text-gray-900\">新規作成</h1>\n"
            "</div>\n\n"
            "<div class=\"bg-white rounded-xl shadow p-8 max-w-2xl\">\n"
            "    @if($errors->any())\n"
            "        <div class=\"mb-6 p-4 bg-red-50 border border-red-300 rounded-lg\">\n"
            "            <p class=\"text-sm font-medium text-red-800 mb-1\">入力エラーがあります</p>\n"
            "            <ul class=\"list-disc list-inside text-sm text-red-700 space-y-1\">\n"
            "                @foreach($errors->all() as $error)\n"
            "                    <li>{{ $error }}</li>\n"
            "                @endforeach\n"
            "            </ul>\n"
            "        </div>\n"
            "    @endif\n\n"
            f"    <form method=\"POST\" action=\"{{{{ route('{route}.store') }}}}\">\n"
            "        @csrf\n\n"
            "        <div class=\"space-y-5\">\n"
            f"            @include('{route}.partials.form')\n"
            "        </div>\n\n"
            "        <div class=\"mt-8 flex gap-3 pt-6 border-t border-gray-100\">\n"
            f"            <button type=\"submit\"\n"
            f"                    class=\"px-6 py-2 {accent['bg']} {accent['bg_hover']} text-white font-medium rounded-lg shadow transition-colors\">\n"
            "                作成する\n"
            "            </button>\n"
            f"            <a href=\"{{{{ route('{route}.index') }}}}\"\n"
            "               class=\"px-6 py-2 bg-white border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors\">\n"
            "                キャンセル\n"
            "            </a>\n"
            "        </div>\n"
            "    </form>\n"
            "</div>\n"
            "@endsection\n"
        )

    # ------------------------------------------------------------------
    # edit.blade.php
    # ------------------------------------------------------------------

    def _render_edit(self, table: TableSchema, accent: dict[str, str]) -> str:
        route = self._route_prefix(table)
        var   = self._var(table)
        return (
            "@extends('layouts.app')\n\n"
            f"@section('title', '{table.table_name} 編集')\n\n"
            "@section('content')\n"
            "<div class=\"mb-6 flex items-center gap-3\">\n"
            f"    <a href=\"{{{{ route('{route}.index') }}}}\" class=\"text-gray-400 hover:text-gray-600 text-sm\">&#8592; 一覧へ戻る</a>\n"
            "    <span class=\"text-gray-300\">/</span>\n"
            "    <h1 class=\"text-2xl font-bold text-gray-900\">編集</h1>\n"
            "</div>\n\n"
            "<div class=\"bg-white rounded-xl shadow p-8 max-w-2xl\">\n"
            "    @if($errors->any())\n"
            "        <div class=\"mb-6 p-4 bg-red-50 border border-red-300 rounded-lg\">\n"
            "            <p class=\"text-sm font-medium text-red-800 mb-1\">入力エラーがあります</p>\n"
            "            <ul class=\"list-disc list-inside text-sm text-red-700 space-y-1\">\n"
            "                @foreach($errors->all() as $error)\n"
            "                    <li>{{ $error }}</li>\n"
            "                @endforeach\n"
            "            </ul>\n"
            "        </div>\n"
            "    @endif\n\n"
            f"    <form method=\"POST\" action=\"{{{{ route('{route}.update', ${var}) }}}}\">\n"
            "        @csrf\n"
            "        @method('PUT')\n\n"
            "        <div class=\"space-y-5\">\n"
            f"            @include('{route}.partials.form')\n"
            "        </div>\n\n"
            "        <div class=\"mt-8 flex gap-3 pt-6 border-t border-gray-100\">\n"
            f"            <button type=\"submit\"\n"
            f"                    class=\"px-6 py-2 {accent['bg']} {accent['bg_hover']} text-white font-medium rounded-lg shadow transition-colors\">\n"
            "                更新する\n"
            "            </button>\n"
            f"            <a href=\"{{{{ route('{route}.show', ${var}) }}}}\"\n"
            "               class=\"px-6 py-2 bg-white border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors\">\n"
            "                キャンセル\n"
            "            </a>\n"
            "        </div>\n"
            "    </form>\n"
            "</div>\n"
            "@endsection\n"
        )

    # ------------------------------------------------------------------
    # show.blade.php
    # ------------------------------------------------------------------

    def _render_show(self, table: TableSchema, accent: dict[str, str]) -> str:
        route = self._route_prefix(table)
        var   = self._var(table)
        cols  = table.columns

        dl_rows = "\n".join(
            f"        <div class=\"px-6 py-4 grid grid-cols-3 gap-4 border-b border-gray-100 last:border-0\">\n"
            f"            <dt class=\"text-sm font-medium text-gray-500\">{self._label(c)}</dt>\n"
            f"            <dd class=\"text-sm text-gray-900 col-span-2\">{{{{ ${var}->{c.name} ?? '&#8212;' }}}}</dd>\n"
            f"        </div>"
            for c in cols
        )

        return (
            "@extends('layouts.app')\n\n"
            f"@section('title', '{table.table_name} 詳細')\n\n"
            "@section('content')\n"
            "<div class=\"mb-6 flex items-center gap-3\">\n"
            f"    <a href=\"{{{{ route('{route}.index') }}}}\" class=\"text-gray-400 hover:text-gray-600 text-sm\">&#8592; 一覧へ戻る</a>\n"
            "    <span class=\"text-gray-300\">/</span>\n"
            "    <h1 class=\"text-2xl font-bold text-gray-900\">詳細</h1>\n"
            "</div>\n\n"
            "<div class=\"bg-white rounded-xl shadow overflow-hidden max-w-3xl\">\n"
            "    <dl class=\"divide-y divide-gray-100\">\n"
            f"{dl_rows}\n"
            "    </dl>\n"
            "</div>\n\n"
            "<div class=\"mt-6 flex gap-3\">\n"
            f"    <a href=\"{{{{ route('{route}.edit', ${var}) }}}}\"\n"
            f"       class=\"px-5 py-2 {accent['bg']} {accent['bg_hover']} text-white font-medium rounded-lg shadow transition-colors\">\n"
            "        編集する\n"
            "    </a>\n"
            f"    <form method=\"POST\" action=\"{{{{ route('{route}.destroy', ${var}) }}}}\"\n"
            "          onsubmit=\"return confirm('削除しますか？')\">\n"
            "        @csrf\n"
            "        @method('DELETE')\n"
            "        <button type=\"submit\"\n"
            "                class=\"px-5 py-2 bg-white border border-red-300 text-red-600 font-medium rounded-lg hover:bg-red-50 transition-colors\">\n"
            "            削除する\n"
            "        </button>\n"
            "    </form>\n"
            f"    <a href=\"{{{{ route('{route}.index') }}}}\"\n"
            "       class=\"px-5 py-2 bg-white border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors\">\n"
            "        一覧へ戻る\n"
            "    </a>\n"
            "</div>\n"
            "@endsection\n"
        )