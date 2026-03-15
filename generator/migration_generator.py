"""Migration file generator."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import re

from .schema_converter import ColumnSchema, TableSchema, map_sql_to_laravel


class MigrationGenerator:
    """Generate Laravel migration files from normalized schemas."""

    def __init__(self, output_root: str | Path) -> None:
        self.output_root = Path(output_root)
        self.migration_dir = self.output_root / "database" / "migrations"

    def generate(self, schemas: list[TableSchema]) -> list[Path]:
        self.migration_dir.mkdir(parents=True, exist_ok=True)

        generated_paths: list[Path] = []
        base_datetime = datetime.now()

        for index, table in enumerate(schemas):
            timestamp = (base_datetime + timedelta(seconds=index)).strftime("%Y_%m_%d_%H%M%S")
            file_name = f"{timestamp}_create_{table.table_name}_table.php"
            file_path = self.migration_dir / file_name
            file_path.write_text(self._render_migration(table), encoding="utf-8")
            generated_paths.append(file_path)

        return generated_paths

    def _render_migration(self, table: TableSchema) -> str:
        column_lines = self._render_columns(table)

        return f"""<?php

use Illuminate\\Database\\Migrations\\Migration;
use Illuminate\\Database\\Schema\\Blueprint;
use Illuminate\\Support\\Facades\\Schema;

return new class extends Migration
{{
    public function up(): void
    {{
        Schema::create('{table.table_name}', function (Blueprint $table) {{
{column_lines}
        }});
    }}

    public function down(): void
    {{
        Schema::dropIfExists('{table.table_name}');
    }}
}};
"""

    def _render_columns(self, table: TableSchema) -> str:
        lines: list[str] = []
        names = {column.name for column in table.columns}

        for column in table.columns:
            lines.append(f"            {self._render_column(column)}")

        if "created_at" not in names and "updated_at" not in names:
            lines.append("            $table->timestamps();")

        return "\n".join(lines)

    def _render_column(self, column: ColumnSchema) -> str:
        if column.primary and column.auto_increment:
            if column.name == "id":
                return "$table->id();"
            return f"$table->id('{column.name}');"

        if column.foreign_key:
            statement = self._render_foreign_key(column)
        else:
            laravel_type = map_sql_to_laravel(column.data_type)
            statement = self._render_standard_column(column, laravel_type)

        if column.nullable:
            statement += "->nullable()"
        if column.default is not None:
            statement += f"->default({self._php_literal(column.default)})"
        if column.comment:
            comment = column.comment.replace("'", "\\'")
            statement += f"->comment('{comment}')"
        if column.primary:
            statement += "->primary()"

        return f"{statement};"

    def _render_standard_column(self, column: ColumnSchema, laravel_type: str) -> str:
        if laravel_type == "string":
            if column.length:
                return f"$table->string('{column.name}', {column.length})"
            return f"$table->string('{column.name}')"

        if laravel_type == "char":
            if column.length:
                return f"$table->char('{column.name}', {column.length})"
            return f"$table->char('{column.name}', 255)"

        if laravel_type == "decimal":
            precision = column.length if column.length else 10
            return f"$table->decimal('{column.name}', {precision}, 2)"

        return f"$table->{laravel_type}('{column.name}')"

    def _render_foreign_key(self, column: ColumnSchema) -> str:
        target_table, target_column = self._resolve_foreign_target(column)

        if target_table is None:
            return f"$table->foreignId('{column.name}')->constrained()"

        return (
            f"$table->foreignId('{column.name}')->constrained('{target_table}', '{target_column}')"
        )

    def _resolve_foreign_target(self, column: ColumnSchema) -> tuple[str | None, str]:
        if column.foreign_key == "__AUTO__":
            inferred = self._infer_foreign_table(column.name)
            return inferred, "id"

        if column.foreign_key and "." in column.foreign_key:
            table_name, column_name = column.foreign_key.split(".", maxsplit=1)
            return table_name.strip(), column_name.strip()

        if column.foreign_key:
            return column.foreign_key.strip(), "id"

        return None, "id"

    @staticmethod
    def _infer_foreign_table(column_name: str) -> str | None:
        if not column_name.endswith("_id"):
            return None
        base = column_name[:-3]
        if not base:
            return None
        if base.endswith("y"):
            return f"{base[:-1]}ies"
        if base.endswith("s"):
            return base
        return f"{base}s"

    @staticmethod
    def _php_literal(value: str) -> str:
        lowered = value.lower()
        if lowered in {"null", "none"}:
            return "null"
        if lowered in {"true", "false"}:
            return lowered
        if re.fullmatch(r"-?\d+(\.\d+)?", value):
            return value
        escaped = value.replace("'", "\\'")
        return f"'{escaped}'"
