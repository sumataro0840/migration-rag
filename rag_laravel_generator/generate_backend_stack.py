"""CLI for generating Laravel backend stack from existing models/migrations."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from rag_laravel_generator.backend_stack_generator import BackendStackGenerator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Controller/Service/Repository/Requests from Laravel models."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Laravel project root path (default: current directory).",
    )
    parser.add_argument(
        "--include-user",
        action="store_true",
        help="Include User model as generation target.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    exclude = set()
    if not args.include_user:
        exclude.add("User")

    generator = BackendStackGenerator(
        project_root=Path(args.root),
        exclude_models=exclude,
    )
    report = generator.generate()

    print("=== Target Models ===")
    if not report.target_models:
        print("(none)")
        return 0

    for model in report.target_models:
        print(f"- {model}")

    print("\n=== Generated Files ===")
    for model in report.target_models:
        paths = report.generated_files.get(model, [])
        if not paths:
            print(f"- {model}: (none)")
            continue
        print(f"- {model}:")
        for path in paths:
            print(f"  - {path}")

    print("\n=== Skipped Existing Files ===")
    for model in report.target_models:
        paths = report.skipped_files.get(model, [])
        if not paths:
            continue
        print(f"- {model}:")
        for path in paths:
            print(f"  - {path}")

    print("\n=== Updated Relations ===")
    if not report.updated_relations:
        print("(none)")
    else:
        for model in sorted(report.updated_relations):
            methods = ", ".join(report.updated_relations[model])
            print(f"- {model}: {methods}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

