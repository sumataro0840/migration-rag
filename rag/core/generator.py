from jinja2 import Template
from models.schema import ParsedRequest, ColumnSpec
from core.validators import validate_request
from core.retriever import retrieve_related_docs

TEMPLATE = Template("""<?php

use Illuminate\\Database\\Migrations\\Migration;
use Illuminate\\Database\\Schema\\Blueprint;
use Illuminate\\Support\\Facades\\Schema;

return new class extends Migration {
    public function up(): void
    {
        Schema::table('{{ table }}', function (Blueprint $table) {
{% for col in columns %}
            $table->{{ col.type }}('{{ col.name }}'{% if col.length %}, {{ col.length }}{% endif %}){% if col.nullable %}->nullable(){% endif %}{% if col.comment %}->comment('{{ col.comment }}'){% endif %};
{% endfor %}
        });
    }

    public function down(): void
    {
        Schema::table('{{ table }}', function (Blueprint $table) {
{% for col in columns %}
            $table->dropColumn('{{ col.name }}');
{% endfor %}
        });
    }
};
""")


def parse_request_text(request_text: str) -> ParsedRequest:
    table = "costs" if "costs" in request_text else "unknown_table"
    col_name = "customer_name" if "customer_name" in request_text else "new_column"
    length = 100 if "100" in request_text else None
    comment = "得意先名" if "得意先名" in request_text else None

    return ParsedRequest(
        table=table,
        operation="add_column",
        columns=[
            ColumnSpec(
                name=col_name,
                type="string",
                length=length,
                nullable=False,
                comment=comment,
            )
        ],
        need_down=("down" in request_text.lower() or "ロールバック" in request_text),
    )


def generate_migration_bundle(request_text: str, project_root: str):
    parsed = parse_request_text(request_text)

    schema_info = {
        "tables": {
            "costs": ["id", "work_no", "project_name"]
        }
    }

    warnings = validate_request(parsed, schema_info)

    retrieved_docs = retrieve_related_docs(parsed, project_root)

    migration_code = TEMPLATE.render(
        table=parsed.table,
        columns=parsed.columns,
    )

    migration_filename = f"2026_03_10_120000_add_{parsed.columns[0].name}_to_{parsed.table}_table.php"

    return {
        "parsed_request": parsed.model_dump(),
        "retrieved_docs": retrieved_docs,
        "migration_filename": migration_filename,
        "migration_code": migration_code,
        "warnings": warnings,
    }