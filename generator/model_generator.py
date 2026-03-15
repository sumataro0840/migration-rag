"""Model file generator."""

from __future__ import annotations

from pathlib import Path

from .schema_converter import TableSchema


class ModelGenerator:
    """Generate Eloquent model classes."""

    def __init__(self, output_root: str | Path) -> None:
        self.output_root = Path(output_root)
        self.model_dir = self.output_root / "app" / "Models"

    def generate(self, schemas: list[TableSchema]) -> list[Path]:
        self.model_dir.mkdir(parents=True, exist_ok=True)

        generated_paths: list[Path] = []
        for table in schemas:
            file_path = self.model_dir / f"{table.model_name}.php"
            file_path.write_text(self._render_model(table), encoding="utf-8")
            generated_paths.append(file_path)

        return generated_paths

    def _render_model(self, table: TableSchema) -> str:
        fillable_columns = [
            column.name
            for column in table.columns
            if not column.primary  # PKはauto_increment有無にかかわらず除外
            and column.name not in {"created_at", "updated_at", "deleted_at"}
        ]

        fillable_lines = "\n".join(f"        '{name}'," for name in fillable_columns)
        if not fillable_lines:
            fillable_lines = "        // No mass-assignable columns inferred from the Excel file."

        # PKが 'id' 以外の場合は $primaryKey を明示
        pk_columns = [c for c in table.columns if c.primary]
        pk_line = ""
        if pk_columns and pk_columns[0].name != "id":
            pk_line = f"\n    protected $primaryKey = '{pk_columns[0].name}';"

        # PKが整数でない場合は incrementing = false
        pk_type = pk_columns[0].data_type.lower() if pk_columns else "bigint"
        incr_line = ""
        if pk_type not in {"integer", "bigint", "smallint", "tinyint", "int"}:
            incr_line = "\n    public $incrementing = false;\n    protected $keyType = 'string';"

        return f"""<?php

namespace App\\Models;

use Illuminate\\Database\\Eloquent\\Factories\\HasFactory;
use Illuminate\\Database\\Eloquent\\Model;

class {table.model_name} extends Model
{{
    use HasFactory;

    protected $table = '{table.table_name}';{pk_line}{incr_line}

    protected $fillable = [
{fillable_lines}
    ];
}}
"""