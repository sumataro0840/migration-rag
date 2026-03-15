#!/usr/bin/env python3
"""CLI: Excel table definitions → Laravel migration/model/controller/routes."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from generator.excel_parser import ExcelParser, ExcelParserError
from generator.schema_converter import SchemaConverter, SchemaConversionError
from generator.migration_generator import MigrationGenerator
from generator.model_generator import ModelGenerator
from generator.controller_generator import ControllerGenerator
from generator.route_generator import RouteGenerator


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate Laravel backend files from an Excel table-definition workbook."
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

    print(f"[1/5] Parsing Excel: {excel_path}")
    try:
        parsed = ExcelParser().parse(excel_path)
    except ExcelParserError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"[2/5] Converting schema ({len(parsed)} table(s) found)")
    try:
        schemas = SchemaConverter().convert(parsed)
    except SchemaConversionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("[3/5] Generating migrations …")
    migration_paths = MigrationGenerator(output_root).generate(schemas)
    for p in migration_paths:
        print(f"  + {p}")

    print("[4/5] Generating models …")
    model_paths = ModelGenerator(output_root).generate(schemas)
    for p in model_paths:
        print(f"  + {p}")

    print("[5/5] Generating controllers & routes …")
    controller_paths = ControllerGenerator(output_root).generate(schemas)
    for p in controller_paths:
        print(f"  + {p}")

    route_path = RouteGenerator(output_root).generate(schemas)
    print(f"  + {route_path}")

    print(f"\nDone! Files written to: {output_root.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())