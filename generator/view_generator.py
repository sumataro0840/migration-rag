"""Blade View file generator for Laravel 11."""

from __future__ import annotations

from pathlib import Path

from .schema_converter import ColumnSchema, TableSchema

# スキップするシステムカラム（フォームに出さない）
_SYSTEM_COLUMNS = {"created_at", "updated_at", "deleted_at"}

# データ型 → HTMLインプットtype のマッピング
_TYPE_MAP: dict[str, str] = {
    "integer":   "number",
    "bigint":    "number",
    "smallint":  "number",
    "tinyint":   "number",
    "int":       "number",
    "float":     "number",
    "double":    "number",
    "decimal":   "number",
    "numeric":   "number",
    "boolean":   "checkbox",
    "bool":      "checkbox",
    "date":      "date",
    "datetime":  "datetime-local",
    "timestamp": "datetime-local",
    "text":      "textarea",
    "mediumtext":"textarea",
    "longtext":  "textarea",
}


class ViewGenerator:
    """Generate Blade view files from normalized TableSchema objects."""

    def __init__(self, output_root: str | Path) -> None:
        self.output_root = Path(output_root)

    def generate(self, schemas: list[TableSchema]) -> list[Path]:
        """全テーブル分のBladeファイルを生成し、生成されたパスのリストを返す。"""
        generated: list[Path] = []
        for table in schemas:
            generated.extend(self._generate_for_table(table))
        return generated

    # ------------------------------------------------------------------
    # テーブル単位の生成
    # ------------------------------------------------------------------

    def _generate_for_table(self, table: TableSchema) -> list[Path]:
        view_dir = self.output_root / "resources" / "views" / table.table_name
        partial_dir = view_dir / "partials"
        view_dir.mkdir(parents=True, exist_ok=True)
        partial_dir.mkdir(parents=True, exist_ok=True)

        files = {
            view_dir / "index.blade.php":          self._render_index(table),
            view_dir / "create.blade.php":         self._render_create(table),
            view_dir / "edit.blade.php":           self._render_edit(table),
            view_dir / "show.blade.php":           self._render_show(table),
            partial_dir / "form.blade.php":        self._render_form(table),
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
        """表示ラベルを決定する。論理名があれば優先、なければカラム名をタイトルケースに変換。"""
        if column.logical_name:
            return column.logical_name
        return column.name.replace("_", " ").title()

    @staticmethod
    def _form_columns(table: TableSchema) -> list[ColumnSchema]:
        """フォームに出力するカラム一覧（PK・システムカラムを除外）。"""
        return [
            col for col in table.columns
            if not col.primary
            and col.name not in _SYSTEM_COLUMNS
        ]

    @staticmethod
    def _display_columns(table: TableSchema) -> list[ColumnSchema]:
        """一覧・詳細表示に使うカラム一覧（全カラム、ただし長文テキストは除外）。"""
        skip_types = {"text", "mediumtext", "longtext"}
        return [
            col for col in table.columns
            if col.data_type.lower() not in skip_types
        ]

    @staticmethod
    def _var(table: TableSchema) -> str:
        """Blade テンプレート内で使う変数名（例: $mCustomer）。"""
        name = table.model_name[0].lower() + table.model_name[1:]
        return name

    @staticmethod
    def _route_prefix(table: TableSchema) -> str:
        """Route名プレフィックス（例: m_customers）。"""
        return table.table_name

    # ------------------------------------------------------------------
    # フォームフィールド単体レンダリング
    # ------------------------------------------------------------------

    def _render_field(self, col: ColumnSchema, table: TableSchema) -> str:
        label    = self._label(col)
        name     = col.name
        var      = self._var(table)
        required = "" if col.nullable else ' required'
        dt       = col.data_type.lower()

        # _id 系 → select（外部キーを想定、プレースホルダーのみ）
        if name.endswith("_id"):
            return self._field_select_fk(name, label, var, required)

        # enum → select
        if dt == "enum":
            return self._field_select_enum(name, label, var, required)

        # boolean → checkbox
        if dt in {"boolean", "bool"}:
            return self._field_checkbox(name, label, var)

        # textarea
        if dt in {"text", "mediumtext", "longtext"}:
            return self._field_textarea(name, label, var, required)

        # その他 → input type を決定
        input_type = _TYPE_MAP.get(dt, "text")
        return self._field_input(name, label, var, input_type, required)

    @staticmethod
    def _field_input(name: str, label: str, var: str, input_type: str, required: str) -> str:
        return (
            f'    <div>\n'
            f'        <x-input-label value="{label}" />\n'
            f'        <input\n'
            f'            type="{input_type}"\n'
            f'            name="{name}"\n'
            f'            value="{{{{ old(\'{name}\', ${var}->{name} ?? \'\') }}}}"\n'
            f'            class="mt-1 w-full border rounded-md p-2"{required}\n'
            f'        >\n'
            f'        @error(\'{name}\')\n'
            f'            <p class="text-red-500 text-xs mt-1">{{{{ $message }}}}</p>\n'
            f'        @enderror\n'
            f'    </div>'
        )

    @staticmethod
    def _field_textarea(name: str, label: str, var: str, required: str) -> str:
        return (
            f'    <div>\n'
            f'        <x-input-label value="{label}" />\n'
            f'        <textarea\n'
            f'            name="{name}"\n'
            f'            class="mt-1 w-full border rounded-md p-2"{required}\n'
            f'        >{{{{ old(\'{name}\', ${var}->{name} ?? \'\') }}}}</textarea>\n'
            f'        @error(\'{name}\')\n'
            f'            <p class="text-red-500 text-xs mt-1">{{{{ $message }}}}</p>\n'
            f'        @enderror\n'
            f'    </div>'
        )

    @staticmethod
    def _field_checkbox(name: str, label: str, var: str) -> str:
        return (
            f'    <div class="flex items-center gap-2">\n'
            f'        <input\n'
            f'            type="checkbox"\n'
            f'            name="{name}"\n'
            f'            value="1"\n'
            f'            {{{{ old(\'{name}\', ${var}->{name} ?? false) ? \'checked\' : \'\' }}}}\n'
            f'            class="rounded border-gray-300"\n'
            f'        >\n'
            f'        <x-input-label value="{label}" />\n'
            f'        @error(\'{name}\')\n'
            f'            <p class="text-red-500 text-xs mt-1">{{{{ $message }}}}</p>\n'
            f'        @enderror\n'
            f'    </div>'
        )

    @staticmethod
    def _field_select_fk(name: str, label: str, var: str, required: str) -> str:
        # 外部キー: コントローラ側で $xxxOptions をコンパクトに渡す慣習に合わせる
        options_var = name[:-3] + "Options"  # customer_id → customerOptions
        return (
            f'    <div>\n'
            f'        <x-input-label value="{label}" />\n'
            f'        <select\n'
            f'            name="{name}"\n'
            f'            class="mt-1 w-full border rounded-md p-2"{required}\n'
            f'        >\n'
            f'            <option value="">-- 選択してください --</option>\n'
            f'            @foreach(${options_var} as $id => $label)\n'
            f'                <option value="{{{{ $id }}}}" {{{{ old(\'{name}\', ${var}->{name} ?? \'\') == $id ? \'selected\' : \'\' }}}}>{{{{ $label }}}}</option>\n'
            f'            @endforeach\n'
            f'        </select>\n'
            f'        @error(\'{name}\')\n'
            f'            <p class="text-red-500 text-xs mt-1">{{{{ $message }}}}</p>\n'
            f'        @enderror\n'
            f'    </div>'
        )

    @staticmethod
    def _field_select_enum(name: str, label: str, var: str, required: str) -> str:
        options_var = name + "Options"
        return (
            f'    <div>\n'
            f'        <x-input-label value="{label}" />\n'
            f'        <select\n'
            f'            name="{name}"\n'
            f'            class="mt-1 w-full border rounded-md p-2"{required}\n'
            f'        >\n'
            f'            <option value="">-- 選択してください --</option>\n'
            f'            @foreach(${options_var} as $value => $display)\n'
            f'                <option value="{{{{ $value }}}}" {{{{ old(\'{name}\', ${var}->{name} ?? \'\') == $value ? \'selected\' : \'\' }}}}>{{{{ $display }}}}</option>\n'
            f'            @endforeach\n'
            f'        </select>\n'
            f'        @error(\'{name}\')\n'
            f'            <p class="text-red-500 text-xs mt-1">{{{{ $message }}}}</p>\n'
            f'        @enderror\n'
            f'    </div>'
        )

    # ------------------------------------------------------------------
    # 各ビューのレンダリング
    # ------------------------------------------------------------------

    def _render_form(self, table: TableSchema) -> str:
        form_cols   = self._form_columns(table)
        fields_html = "\n\n".join(self._render_field(col, table) for col in form_cols)

        return (
            f'{{-- {table.table_name} partials/form.blade.php --}}\n'
            f'{{-- このファイルは create / edit から @include されます --}}\n\n'
            f'{fields_html}\n'
        )

    def _render_index(self, table: TableSchema) -> str:
        route   = self._route_prefix(table)
        var     = self._var(table)
        disp    = self._display_columns(table)

        # <th> ヘッダー行
        th_rows = "\n".join(
            f"                <th class=\"px-4 py-2 text-left\">{self._label(c)}</th>"
            for c in disp
        )
        th_rows += "\n                <th class=\"px-4 py-2\"></th>"

        # <td> データ行
        td_rows = "\n".join(
            f"                    <td class=\"px-4 py-2\">{{{{ $item->{c.name} }}}}</td>"
            for c in disp
        )
        td_rows += (
            f"\n                    <td class=\"px-4 py-2 space-x-2\">\n"
            f"                        <a href=\"{{{{ route('{route}.show', $item) }}}}\" class=\"text-blue-600 hover:underline\">詳細</a>\n"
            f"                        <a href=\"{{{{ route('{route}.edit', $item) }}}}\" class=\"text-yellow-600 hover:underline\">編集</a>\n"
            f"                        <form method=\"POST\" action=\"{{{{ route('{route}.destroy', $item) }}}}\" class=\"inline\"\n"
            f"                              onsubmit=\"return confirm('削除しますか？')\">\n"
            f"                            @csrf\n"
            f"                            @method('DELETE')\n"
            f"                            <button type=\"submit\" class=\"text-red-600 hover:underline\">削除</button>\n"
            f"                        </form>\n"
            f"                    </td>"
        )

        return f"""\
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>{table.table_name} 一覧</title>
</head>
<body>

<div class="p-6">
    <div class="flex justify-between items-center mb-4">
        <h1 class="text-2xl font-bold">{table.table_name} 一覧</h1>
        <a href="{{{{ route('{route}.create') }}}}" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
            新規作成
        </a>
    </div>

    @if(session('success'))
        <p class="mb-4 text-green-600">{{{{ session('success') }}}}</p>
    @endif

    <table class="w-full border-collapse border border-gray-300">
        <thead class="bg-gray-100">
            <tr>
{th_rows}
            </tr>
        </thead>
        <tbody>
            @forelse($items as $item)
            <tr class="border-t hover:bg-gray-50">
{td_rows}
            </tr>
            @empty
            <tr>
                <td colspan="{len(disp) + 1}" class="px-4 py-6 text-center text-gray-500">データがありません</td>
            </tr>
            @endforelse
        </tbody>
    </table>

    <div class="mt-4">
        {{{{ $items->links() }}}}
    </div>
</div>

</body>
</html>
"""

    def _render_create(self, table: TableSchema) -> str:
        route = self._route_prefix(table)

        return f"""\
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>{table.table_name} 新規作成</title>
</head>
<body>

<div class="p-6 max-w-2xl mx-auto">
    <h1 class="text-2xl font-bold mb-6">{table.table_name} 新規作成</h1>

    @if($errors->any())
        <div class="mb-4 p-4 bg-red-50 border border-red-300 rounded">
            <ul class="list-disc list-inside text-red-600 text-sm">
                @foreach($errors->all() as $error)
                    <li>{{{{ $error }}}}</li>
                @endforeach
            </ul>
        </div>
    @endif

    <form method="POST" action="{{{{ route('{route}.store') }}}}">
        @csrf

        <div class="space-y-4">
            @include('{route}.partials.form')
        </div>

        <div class="mt-6 flex gap-4">
            <button type="submit" class="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                作成
            </button>
            <a href="{{{{ route('{route}.index') }}}}" class="px-6 py-2 bg-gray-200 rounded hover:bg-gray-300">
                キャンセル
            </a>
        </div>
    </form>
</div>

</body>
</html>
"""

    def _render_edit(self, table: TableSchema) -> str:
        route = self._route_prefix(table)
        var   = self._var(table)

        return f"""\
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>{table.table_name} 編集</title>
</head>
<body>

<div class="p-6 max-w-2xl mx-auto">
    <h1 class="text-2xl font-bold mb-6">{table.table_name} 編集</h1>

    @if($errors->any())
        <div class="mb-4 p-4 bg-red-50 border border-red-300 rounded">
            <ul class="list-disc list-inside text-red-600 text-sm">
                @foreach($errors->all() as $error)
                    <li>{{{{ $error }}}}</li>
                @endforeach
            </ul>
        </div>
    @endif

    <form method="POST" action="{{{{ route('{route}.update', ${var}) }}}}">
        @csrf
        @method('PUT')

        <div class="space-y-4">
            @include('{route}.partials.form')
        </div>

        <div class="mt-6 flex gap-4">
            <button type="submit" class="px-6 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600">
                更新
            </button>
            <a href="{{{{ route('{route}.index') }}}}" class="px-6 py-2 bg-gray-200 rounded hover:bg-gray-300">
                キャンセル
            </a>
        </div>
    </form>
</div>

</body>
</html>
"""

    def _render_show(self, table: TableSchema) -> str:
        route = self._route_prefix(table)
        var   = self._var(table)
        cols  = table.columns

        # 全カラムを定義リスト形式で表示
        dl_rows = "\n".join(
            f"        <div class=\"py-2 border-b\">\n"
            f"            <dt class=\"text-sm text-gray-500\">{self._label(c)}</dt>\n"
            f"            <dd class=\"mt-1 text-gray-900\">{{{{ ${var}->{c.name} }}}}</dd>\n"
            f"        </div>"
            for c in cols
        )

        return f"""\
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>{table.table_name} 詳細</title>
</head>
<body>

<div class="p-6 max-w-2xl mx-auto">
    <h1 class="text-2xl font-bold mb-6">{table.table_name} 詳細</h1>

    <dl class="divide-y divide-gray-200">
{dl_rows}
    </dl>

    <div class="mt-6 flex gap-4">
        <a href="{{{{ route('{route}.edit', ${var}) }}}}" class="px-6 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600">
            編集
        </a>
        <form method="POST" action="{{{{ route('{route}.destroy', ${var}) }}}}"
              onsubmit="return confirm('削除しますか？')">
            @csrf
            @method('DELETE')
            <button type="submit" class="px-6 py-2 bg-red-600 text-white rounded hover:bg-red-700">
                削除
            </button>
        </form>
        <a href="{{{{ route('{route}.index') }}}}" class="px-6 py-2 bg-gray-200 rounded hover:bg-gray-300">
            一覧へ戻る
        </a>
    </div>
</div>

</body>
</html>
"""