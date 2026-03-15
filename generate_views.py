#!/usr/bin/env python3
"""CLI: Excel table definitions → Laravel Blade views.

既存の generate_laravel_app.py とは独立したスタンドアロンCLIです。
Migration/Model/Controller は生成せず、Blade View のみを出力します。

使用例:
    python3 generate_views.py tables.xlsx
    python3 generate_views.py tables.xlsx --output laravel_output
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from generator.excel_parser import ExcelParser, ExcelParserError
from generator.schema_converter import SchemaConverter, SchemaConversionError
from generator.view_generator import ViewGenerator


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate Laravel Blade view files from an Excel table-definition workbook."
    )
    p.add_argument("excel", help="Path to the Excel file (.xlsx).")
    p.add_argument(
        "--output",
        default="laravel_output",
        help="Root directory for generated files (default: laravel_output).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    excel_path = Path(args.excel)
    output_root = Path(args.output)

    print(f"[1/3] Parsing Excel: {excel_path}")
    try:
        parsed = ExcelParser().parse(excel_path)
    except ExcelParserError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"[2/3] Converting schema ({len(parsed)} table(s) found)")
    try:
        schemas = SchemaConverter().convert(parsed)
    except SchemaConversionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("[3/3] Generating Blade views …")
    view_paths = ViewGenerator(output_root).generate(schemas)
    for p in view_paths:
        print(f"  + {p}")

    print(f"\nDone! Views written to: {(output_root / 'resources' / 'views').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())