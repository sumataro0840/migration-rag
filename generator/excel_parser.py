"""Excel parser for Laravel code generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import pandas as pd
except ModuleNotFoundError:
    pd = None


class ExcelParserError(Exception):
    """Raised when Excel parsing fails."""


class ExcelParser:
    """Parse multi-sheet Excel files that define table columns.

    実際のフォーマット想定:
    - 行0-4: テーブルメタ情報（テーブル名など）
    - 行5  : カラムヘッダー行
    - 行6- : カラム定義行
    - 「変更履歴」など非テーブルシートは自動スキップ
    """

    _TABLE_NAME_ROW = 1
    _TABLE_NAME_COL = 8  # "テーブル名" 物理名が入る列

    _HEADER_ALIASES: dict[str, set[str]] = {
        "no": {"no", "no.", "番号"},
        "logical_name": {"logicalname", "logical_name", "logical name", "論理名", "日本語名称"},
        "column_name": {
            "columnname", "column_name", "column name",
            "physicalname", "physical_name", "physical name",
            "カラム名", "物理名", "列名",
        },
        "data_type": {"datatype", "data_type", "data type", "型", "データ型", "列タイプ"},
        "length": {"length", "len", "桁数", "長さ", "桁数(小数)"},
        "nullable": {
            "nullable", "null", "null許可", "null許容", "nullable?",
            "notnull", "not null", "not\nnull",
        },
        "default": {"default", "defaultvalue", "default value", "デフォルト", "初期値"},
        "primary_key": {"primarykey", "primary_key", "primary key", "pk", "主キー"},
        "auto_increment": {
            "autoincrement", "auto_increment", "auto increment",
            "identity", "自動採番", "採番",
        },
        "foreign_key": {"foreignkey", "foreign_key", "foreign key", "fk", "外部キー"},
        "comment": {"comment", "comments", "備考", "コメント", "説明／備考"},
        "db_constraint": {"dbconstraint", "db_constraint", "ＤＢ制約", "db制約"},
    }

    _REQUIRED_COLUMNS = {"column_name", "data_type"}
    _SKIP_SHEET_PATTERNS = {"変更履歴", "changelog", "history", "revision", "改訂"}

    def parse(self, excel_path: str | Path) -> dict[str, list[dict[str, Any]]]:
        if pd is None:
            raise ExcelParserError(
                "Missing dependency: pandas/openpyxl. Install with `pip install pandas openpyxl`."
            )

        path = Path(excel_path)
        if not path.exists():
            raise ExcelParserError(f"Excel file was not found: {path}")

        try:
            workbook = pd.ExcelFile(path, engine="openpyxl")
        except Exception as exc:
            raise ExcelParserError(f"Failed to open Excel file: {path}") from exc

        result: dict[str, list[dict[str, Any]]] = {}

        for sheet_name in workbook.sheet_names:
            if self._should_skip_sheet(sheet_name):
                continue

            try:
                rows = self._parse_sheet(workbook, sheet_name)
            except ExcelParserError:
                raise
            except Exception as exc:
                raise ExcelParserError(
                    f"Sheet '{sheet_name}' の解析中にエラー: {exc}"
                ) from exc

            if rows:
                table_key = self._extract_table_name(workbook, sheet_name) or sheet_name
                result[table_key] = rows

        if not result:
            raise ExcelParserError("No valid sheet definitions were found in the Excel file.")

        return result

    def _should_skip_sheet(self, sheet_name: str) -> bool:
        normalized = sheet_name.strip().lower()
        return any(pattern in normalized for pattern in self._SKIP_SHEET_PATTERNS)

    def _extract_table_name(self, workbook: Any, sheet_name: str) -> str | None:
        try:
            df_raw = pd.read_excel(workbook, sheet_name=sheet_name, header=None, dtype=object)
            if len(df_raw) > self._TABLE_NAME_ROW and len(df_raw.columns) > self._TABLE_NAME_COL:
                val = df_raw.iloc[self._TABLE_NAME_ROW, self._TABLE_NAME_COL]
                if val is not None and not (isinstance(val, float) and pd.isna(val)):
                    name = str(val).strip()
                    if name:
                        return name
        except Exception:
            pass
        return None

    def _parse_sheet(self, workbook: Any, sheet_name: str) -> list[dict[str, Any]]:
        df_raw = pd.read_excel(workbook, sheet_name=sheet_name, header=None, dtype=object)
        if df_raw.empty:
            return []

        header_row_idx = self._find_header_row(df_raw)
        if header_row_idx is None:
            return []

        header = df_raw.iloc[header_row_idx].tolist()
        data = df_raw.iloc[header_row_idx + 1:].reset_index(drop=True)
        data.columns = range(len(header))

        col_map = self._build_header_map(header)
        renamed = data.rename(columns=col_map)

        missing = self._REQUIRED_COLUMNS - set(renamed.columns)
        if missing:
            raise ExcelParserError(
                f"Sheet '{sheet_name}' is missing required columns: {sorted(missing)}"
            )

        rows: list[dict[str, Any]] = []
        for _, row in renamed.iterrows():
            col_name = self._clean_value(row.get("column_name"))
            data_type = self._clean_value(row.get("data_type"))

            if not col_name and not data_type:
                continue

            nullable_raw = self._clean_value(row.get("nullable"))
            nullable = self._parse_nullable(nullable_raw)

            db_constraint = str(self._clean_value(row.get("db_constraint")) or "")
            primary_key_raw = self._clean_value(row.get("primary_key"))
            primary_key = self._parse_flag(primary_key_raw) or ("PRIMARY KEY" in db_constraint.upper())

            foreign_key_raw = self._clean_value(row.get("foreign_key"))
            fk_value = self._resolve_foreign_key(foreign_key_raw, db_constraint)

            rows.append({
                "no": self._clean_value(row.get("no")),
                "logical_name": self._clean_value(row.get("logical_name")),
                "column_name": col_name,
                "data_type": data_type,
                "length": self._clean_value(row.get("length")),
                "nullable": nullable,
                "default": self._clean_value(row.get("default")),
                "primary_key": primary_key,
                "auto_increment": self._parse_flag(self._clean_value(row.get("auto_increment"))),
                "foreign_key": fk_value,
                "comment": self._clean_value(row.get("comment")),
            })

        return rows

    def _find_header_row(self, df: Any) -> int | None:
        col_aliases = self._HEADER_ALIASES["column_name"]
        type_aliases = self._HEADER_ALIASES["data_type"]

        for idx in range(len(df)):
            row = df.iloc[idx]
            normalized_cells = {self._normalize_header(v) for v in row}
            if normalized_cells & col_aliases and normalized_cells & type_aliases:
                return idx

        return None

    def _build_header_map(self, raw_headers: list[Any]) -> dict[int, str]:
        mapped: dict[int, str] = {}
        for col_idx, raw_header in enumerate(raw_headers):
            cleaned = self._normalize_header(raw_header)
            for canonical, aliases in self._HEADER_ALIASES.items():
                if cleaned in aliases:
                    mapped[col_idx] = canonical
                    break
        return mapped

    @staticmethod
    def _normalize_header(value: Any) -> str:
        if value is None:
            return ""
        return (
            str(value)
            .strip()
            .replace("　", " ")
            .replace("\n", "")
            .replace("_", "")
            .replace("-", "")
            .replace(" ", "")
            .lower()
        )

    @staticmethod
    def _clean_value(value: Any) -> Any:
        if value is None:
            return None
        if pd is not None:
            try:
                if pd.isna(value):
                    return None
            except (TypeError, ValueError):
                pass
        if isinstance(value, str):
            stripped = value.strip()
            return stripped if stripped else None
        return value

    @staticmethod
    def _parse_flag(value: Any) -> bool:
        if value is None:
            return False
        normalized = str(value).strip().lower()
        return normalized in {"〇", "○", "yes", "true", "1", "y", "✓", "✔"}

    @staticmethod
    def _parse_nullable(value: Any) -> bool | None:
        """NOT NULL列の〇 → nullable=False、空 → None（SchemaConverterのデフォルト適用）"""
        if value is None:
            return None
        normalized = str(value).strip().lower()
        if normalized in {"〇", "○", "yes", "true", "1", "y", "✓", "✔"}:
            return False  # NOT NULL列に〇があるので nullable=False
        return None

    @staticmethod
    def _resolve_foreign_key(fk_raw: Any, db_constraint: str) -> Any:
        if fk_raw is not None:
            normalized = str(fk_raw).strip().lower()
            if normalized in {"〇", "○", "yes", "true", "1", "y"}:
                return "__AUTO__"
            if fk_raw:
                return fk_raw

        if db_constraint:
            import re
            m = re.search(r"fk\s*->\s*([\w]+\.[\w]+)", db_constraint, re.IGNORECASE)
            if m:
                return m.group(1)

        return None