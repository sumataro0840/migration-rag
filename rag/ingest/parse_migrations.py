from pathlib import Path
import re

def parse_migration_file(path: str):
    text = Path(path).read_text(encoding="utf-8", errors="ignore")

    table_match = re.search(r"Schema::(?:create|table)\\('([^']+)'", text)
    table_name = table_match.group(1) if table_match else None

    columns = re.findall(r"\\$table->\\w+\\('([^']+)'", text)

    action = "create_table" if "Schema::create(" in text else "add_column" if "Schema::table(" in text else "unknown"

    return {
        "file_path": path,
        "table_name": table_name,
        "action": action,
        "columns": columns,
        "content": text[:2000],
    }