"""Ingest table definitions from Excel and convert to text documents."""

from __future__ import annotations

import sys
from pathlib import Path

# スクリプトとして直接実行されたとき用にパスを追加
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from dataclasses import dataclass
from typing import Any

from generator.excel_parser import ExcelParser
from generator.schema_converter import SchemaConverter, TableSchema


@dataclass(slots=True)
class TableDocument:
    table_name: str
    columns: list[str]
    schema_text: str


def ingest_schemas_from_excel(excel_path: str | Path) -> list[TableDocument]:
    """Load Excel table definitions and return text documents for RAG."""
    parser = ExcelParser()
    parsed = parser.parse(str(excel_path))
    converter = SchemaConverter()
    tables = converter.convert(parsed)

    docs: list[TableDocument] = []
    for table in tables:
        docs.append(table_schema_to_document(table))
    return docs


def table_schema_to_document(table: TableSchema) -> TableDocument:
    """Convert a table schema object to a simple schema text doc."""
    lines: list[str] = [f"Table: {table.table_name}"]
    column_texts: list[str] = []

    for col in table.columns:
        column_line = f"Column: {col.name} {col.data_type}"
        if col.length is not None:
            column_line += f"({col.length})"
        if col.primary:
            column_line += " primary key"
        if col.auto_increment:
            column_line += " auto_increment"
        if col.nullable:
            column_line += " nullable"
        if col.default is not None:
            column_line += f" default={col.default}"
        if col.foreign_key:
            column_line += f" foreign_key={col.foreign_key}"
        lines.append(column_line)
        column_texts.append(column_line)

    schema_text = "\n".join(lines)
    return TableDocument(
        table_name=table.table_name,
        columns=column_texts,
        schema_text=schema_text,
    )


# ingest_excel.py 単体で実行できるように
# 旧コードで table_schema_to_text という名前で参照していたケースへの互換エイリアス
table_schema_to_text = table_schema_to_document


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ingest_excel.py <excel_path>")
        sys.exit(1)

    docs = ingest_schemas_from_excel(sys.argv[1])
    for doc in docs:
        print(doc.schema_text)
        print("---")