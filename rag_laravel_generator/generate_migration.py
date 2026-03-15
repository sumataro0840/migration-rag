#!/usr/bin/env python3
"""CLI: テーブル名を指定してマイグレーションを生成する。

RAG（OpenAI/Chroma）が利用可能な場合はLLMで生成し、
利用不可の場合はExcel定義から直接生成する（フォールバック）。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# スクリプト直接実行時用
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.excel_parser import ExcelParser
from generator.schema_converter import SchemaConverter
from generator.migration_generator import MigrationGenerator


EXCEL_PATH_DEFAULT = Path(__file__).parent.parent / "tables.xlsx"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="指定テーブルのLaravelマイグレーションを生成する。"
    )
    p.add_argument("table", help="生成対象のテーブル名（部分一致）")
    p.add_argument(
        "--excel",
        default=str(EXCEL_PATH_DEFAULT),
        help=f"Excel定義ファイルのパス (default: {EXCEL_PATH_DEFAULT})",
    )
    p.add_argument(
        "--output",
        default="laravel_output",
        help="出力先ディレクトリ (default: laravel_output)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    excel_path = Path(args.excel)
    if not excel_path.exists():
        print(f"ERROR: Excel file not found: {excel_path}", file=sys.stderr)
        print("--excel オプションでパスを指定してください。", file=sys.stderr)
        return 1

    parsed = ExcelParser().parse(excel_path)
    schemas = SchemaConverter().convert(parsed)

    target_query = args.table.lower()
    matched = [s for s in schemas if target_query in s.table_name.lower()]

    if not matched:
        available = ", ".join(s.table_name for s in schemas)
        print(f"ERROR: テーブル '{args.table}' が見つかりません。", file=sys.stderr)
        print(f"利用可能なテーブル: {available}", file=sys.stderr)
        return 1

    paths = MigrationGenerator(args.output).generate(matched)
    for p in paths:
        print(f"Generated: {p}")

    return 0


if __name__ == "__main__":
    sys.exit(main())