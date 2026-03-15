"""Schema conversion layer from normalized Excel rows to domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import re
from typing import Any


class SchemaConversionError(Exception):
    """Raised when conversion to schema objects fails."""


SQL_TO_LARAVEL_TYPE: dict[str, str] = {
    "varchar": "string",
    "char": "char",
    "nvarchar": "string",
    "text": "text",
    "mediumtext": "mediumText",
    "longtext": "longText",
    "bigint": "bigInteger",
    "int": "integer",
    "integer": "integer",
    "smallint": "smallInteger",
    "tinyint": "tinyInteger",
    "boolean": "boolean",
    "bool": "boolean",
    "decimal": "decimal",
    "numeric": "decimal",
    "float": "float",
    "double": "double",
    "timestamp": "timestamp",
    "datetime": "dateTime",
    "date": "date",
    "time": "time",
    "json": "json",
    "uuid": "uuid",
    "binary": "binary",
}


@dataclass(slots=True)
class ColumnSchema:
    """Normalized column metadata for code generation."""

    logical_name: str | None
    name: str
    data_type: str
    length: int | None
    nullable: bool
    default: str | None
    primary: bool
    auto_increment: bool
    foreign_key: str | None
    comment: str | None


@dataclass(slots=True)
class TableSchema:
    """Normalized table metadata for code generation."""

    sheet_name: str
    table_name: str
    model_name: str
    columns: list[ColumnSchema]


class SchemaConverter:
    """Convert raw parsed Excel rows into strongly typed schema objects."""

    def convert(self, parsed_tables: dict[str, list[dict[str, Any]]]) -> list[TableSchema]:
        tables: list[TableSchema] = []
        fallback_counter = 1

        for sheet_name, rows in parsed_tables.items():
            table_name = self._to_table_name(sheet_name)
            if not table_name:
                table_name = f"table_{fallback_counter}"
                fallback_counter += 1

            model_name = self._to_model_name(table_name)
            columns: list[ColumnSchema] = []

            for row in rows:
                column_name = self._normalize_identifier(row.get("column_name"))
                if not column_name:
                    raise SchemaConversionError(
                        f"Sheet '{sheet_name}' has a row without a valid column_name."
                    )

                sql_type = self._normalize_sql_type(row.get("data_type"))
                if not sql_type:
                    raise SchemaConversionError(
                        f"Sheet '{sheet_name}' column '{column_name}' has no valid data_type."
                    )

                columns.append(
                    ColumnSchema(
                        logical_name=self._to_optional_str(row.get("logical_name")),
                        name=column_name,
                        data_type=sql_type,
                        length=self._to_optional_int(row.get("length")),
                        nullable=self._to_bool(row.get("nullable"), default=False),
                        default=self._to_optional_str(row.get("default")),
                        primary=self._to_bool(row.get("primary_key"), default=False),
                        auto_increment=self._to_bool(row.get("auto_increment"), default=False),
                        foreign_key=self._normalize_foreign_key(row.get("foreign_key")),
                        comment=self._to_optional_str(row.get("comment")),
                    )
                )

            if not columns:
                raise SchemaConversionError(f"Sheet '{sheet_name}' did not contain any columns.")

            tables.append(
                TableSchema(
                    sheet_name=sheet_name,
                    table_name=table_name,
                    model_name=model_name,
                    columns=columns,
                )
            )

        return tables

    def to_json(self, schemas: list[TableSchema]) -> list[dict[str, Any]]:
        """Create JSON-serializable schema output."""
        return [
            {
                "sheet": table.sheet_name,
                "table": table.table_name,
                "model": table.model_name,
                "columns": [asdict(column) for column in table.columns],
            }
            for table in schemas
        ]

    def save_json(self, schemas: list[TableSchema], output_path: str | Path) -> Path:
        """Persist schema JSON for inspection/debugging."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(self.to_json(schemas), file, ensure_ascii=False, indent=2)
        return path

    @staticmethod
    def _to_table_name(sheet_name: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9]+", "_", sheet_name).strip("_").lower()
        if not normalized:
            return ""
        return SchemaConverter._pluralize(normalized)

    @staticmethod
    def _to_model_name(table_name: str) -> str:
        singular = SchemaConverter._singularize(table_name)
        return "".join(part.capitalize() for part in singular.split("_") if part)

    @staticmethod
    def _pluralize(word: str) -> str:
        if word.endswith("ies"):
            return word
        if word.endswith("y") and len(word) > 1:
            return f"{word[:-1]}ies"
        if word.endswith("s"):
            return word
        return f"{word}s"

    @staticmethod
    def _singularize(word: str) -> str:
        if word.endswith("ies") and len(word) > 3:
            return f"{word[:-3]}y"
        # 末尾が "ss" の場合（address, process, class など）は削らない
        if word.endswith("ss"):
            return word
        if word.endswith("s") and len(word) > 1:
            return word[:-1]
        return word

    @staticmethod
    def _normalize_identifier(value: Any) -> str:
        if value is None:
            return ""
        identifier = str(value).strip().lower()
        identifier = re.sub(r"\s+", "_", identifier)
        identifier = re.sub(r"[^a-z0-9_]", "", identifier)
        return identifier

    @staticmethod
    def _normalize_sql_type(value: Any) -> str:
        if value is None:
            return ""
        raw = str(value).strip().lower()
        # Handles values like "varchar(255)" or "decimal(10,2)".
        matched = re.match(r"([a-z]+)", raw)
        return matched.group(1) if matched else raw

    @staticmethod
    def _normalize_foreign_key(value: Any) -> str | None:
        as_text = SchemaConverter._to_optional_str(value)
        if as_text is None:
            return None

        normalized = as_text.strip()
        if normalized.lower() in {"yes", "true", "1", "y"}:
            return "__AUTO__"

        return normalized

    @staticmethod
    def _to_optional_str(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text if text else None

    @staticmethod
    def _to_optional_int(value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        text = str(value).strip()
        if not text:
            return None
        try:
            return int(float(text))
        except ValueError:
            return None

    @staticmethod
    def _to_bool(value: Any, *, default: bool = False) -> bool:
        if value is None:
            return default
        if isinstance(value, bool):
            return value

        normalized = str(value).strip().lower()
        if normalized in {"1", "yes", "true", "y", "required", "not null", "no"}:
            return normalized != "no"
        if normalized in {"0", "false", "n", "nullable", "null", ""}:
            return False
        return default


def map_sql_to_laravel(sql_type: str) -> str:
    """Map SQL type strings to Laravel Blueprint type methods."""
    return SQL_TO_LARAVEL_TYPE.get(sql_type.lower(), "string")