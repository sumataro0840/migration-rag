"""Generate Laravel backend stack from existing models and migrations.

This module intentionally lives under rag_laravel_generator so we can keep
the existing migration/model generators untouched and add a new generation flow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re


AUDIT_COLUMNS = {"created_at", "updated_at", "deleted_at"}


@dataclass(slots=True)
class ColumnInfo:
    name: str
    data_type: str
    nullable: bool = False
    default: str | None = None
    foreign_table: str | None = None
    foreign_column: str = "id"
    length: int | None = None


@dataclass(slots=True)
class ModelInfo:
    class_name: str
    table_name: str
    path: Path
    fillable: list[str]
    methods: set[str]


@dataclass(slots=True)
class FieldSpec:
    name: str
    data_type: str
    nullable: bool
    required: bool
    length: int | None = None
    foreign_table: str | None = None
    foreign_column: str = "id"


@dataclass(slots=True)
class GenerationReport:
    target_models: list[str] = field(default_factory=list)
    generated_files: dict[str, list[Path]] = field(default_factory=dict)
    skipped_files: dict[str, list[Path]] = field(default_factory=dict)
    updated_relations: dict[str, list[str]] = field(default_factory=dict)


class BackendStackGenerator:
    """Generate Controller/Service/Repository/Request classes from models."""

    def __init__(
        self,
        project_root: str | Path = ".",
        *,
        exclude_models: set[str] | None = None,
    ) -> None:
        self.project_root = Path(project_root)
        self.exclude_models = set(exclude_models or {"User"})
        self._schema_by_table = self._collect_schema_from_migrations()

    def generate(self) -> GenerationReport:
        models = self._discover_models()
        if not models:
            return GenerationReport()

        model_by_name = {model.class_name: model for model in models}
        model_by_table = {model.table_name: model for model in models}

        report = GenerationReport()

        targets: list[ModelInfo] = []
        for model in models:
            columns = self._schema_by_table.get(model.table_name, {})
            if self._is_excluded_model(model, columns):
                continue
            targets.append(model)

        for model in targets:
            report.target_models.append(model.class_name)
            report.generated_files.setdefault(model.class_name, [])
            report.skipped_files.setdefault(model.class_name, [])

            fields = self._build_field_specs(model)

            requests_dir = (
                self.project_root / "app" / "Http" / "Requests" / model.class_name
            )
            controller_dir = self.project_root / "app" / "Http" / "Controllers"
            services_dir = self.project_root / "app" / "Services"
            repositories_dir = self.project_root / "app" / "Repositories"

            controller_dir.mkdir(parents=True, exist_ok=True)
            services_dir.mkdir(parents=True, exist_ok=True)
            repositories_dir.mkdir(parents=True, exist_ok=True)
            requests_dir.mkdir(parents=True, exist_ok=True)

            candidates = [
                (
                    controller_dir / f"{model.class_name}Controller.php",
                    self._render_controller(model),
                ),
                (
                    services_dir / f"{model.class_name}Service.php",
                    self._render_service(model),
                ),
                (
                    repositories_dir / f"{model.class_name}Repository.php",
                    self._render_repository(model, fields),
                ),
                (
                    requests_dir / f"Save{model.class_name}Request.php",
                    self._render_save_request(model, fields),
                ),
                (
                    requests_dir / f"Search{model.class_name}Request.php",
                    self._render_search_request(model, fields),
                ),
            ]

            for path, content in candidates:
                if path.exists():
                    report.skipped_files[model.class_name].append(path)
                    continue
                path.write_text(content, encoding="utf-8")
                report.generated_files[model.class_name].append(path)

        report.updated_relations = self._append_model_relations(
            targets=targets,
            model_by_name=model_by_name,
            model_by_table=model_by_table,
        )
        return report

    def _discover_models(self) -> list[ModelInfo]:
        model_dir = self.project_root / "app" / "Models"
        if not model_dir.exists():
            return []

        discovered: list[ModelInfo] = []
        for path in sorted(model_dir.rglob("*.php")):
            text = path.read_text(encoding="utf-8")
            class_match = re.search(r"class\s+([A-Za-z0-9_]+)\s+extends\s+[A-Za-z0-9_\\]+", text)
            if not class_match:
                continue

            class_name = class_match.group(1)
            table_name = self._extract_table_name(text) or self._table_from_model_name(class_name)
            fillable = self._extract_fillable(text)
            methods = set(re.findall(r"function\s+([A-Za-z0-9_]+)\s*\(", text))
            discovered.append(
                ModelInfo(
                    class_name=class_name,
                    table_name=table_name,
                    path=path,
                    fillable=fillable,
                    methods=methods,
                )
            )

        return discovered

    def _is_excluded_model(self, model: ModelInfo, columns: dict[str, ColumnInfo]) -> bool:
        if model.class_name in self.exclude_models:
            return True
        if re.search(r"(Log|History|Audit|Pivot)$", model.class_name):
            return True
        if re.search(r"(^|_)(logs?|histories|history|audits?)($|_)", model.table_name):
            return True
        if self._looks_like_pivot(columns):
            return True
        return False

    @staticmethod
    def _looks_like_pivot(columns: dict[str, ColumnInfo]) -> bool:
        if not columns:
            return False
        names = list(columns.keys())
        id_like = [name for name in names if name.endswith("_id")]
        non_audit = [name for name in names if name not in AUDIT_COLUMNS]
        others = [name for name in non_audit if not name.endswith("_id")]
        return len(id_like) >= 2 and not others and "id" not in names

    def _collect_schema_from_migrations(self) -> dict[str, dict[str, ColumnInfo]]:
        migration_dir = self.project_root / "database" / "migrations"
        if not migration_dir.exists():
            return {}

        schema_by_table: dict[str, dict[str, ColumnInfo]] = {}
        pattern = re.compile(
            r"Schema::(?:create|table)\(\s*'([^']+)'\s*,\s*function\s*\(Blueprint \$table\)\s*\{(.*?)\}\s*\);",
            re.DOTALL,
        )

        for migration in sorted(migration_dir.glob("*.php")):
            text = migration.read_text(encoding="utf-8")
            for table_name, block in pattern.findall(text):
                table_columns = schema_by_table.setdefault(table_name, {})
                for statement in re.findall(r"\$table->[^;]+;", block, flags=re.DOTALL):
                    for parsed in self._parse_column_statement(statement):
                        existing = table_columns.get(parsed.name)
                        if existing is None:
                            table_columns[parsed.name] = parsed
                            continue
                        table_columns[parsed.name] = self._merge_column(existing, parsed)

        return schema_by_table

    @staticmethod
    def _merge_column(existing: ColumnInfo, incoming: ColumnInfo) -> ColumnInfo:
        return ColumnInfo(
            name=existing.name,
            data_type=existing.data_type if existing.data_type != "foreign" else incoming.data_type,
            nullable=existing.nullable or incoming.nullable,
            default=existing.default or incoming.default,
            foreign_table=existing.foreign_table or incoming.foreign_table,
            foreign_column=existing.foreign_column if existing.foreign_table else incoming.foreign_column,
            length=existing.length or incoming.length,
        )

    def _parse_column_statement(self, statement: str) -> list[ColumnInfo]:
        statement = " ".join(statement.split())
        if "$table->timestamps()" in statement:
            return [
                ColumnInfo(name="created_at", data_type="timestamp", nullable=True),
                ColumnInfo(name="updated_at", data_type="timestamp", nullable=True),
            ]
        if "$table->softDeletes()" in statement:
            return [ColumnInfo(name="deleted_at", data_type="timestamp", nullable=True)]

        method_match = re.search(r"\$table->([A-Za-z0-9_]+)\(", statement)
        if not method_match:
            return []
        method = method_match.group(1)

        if method == "id":
            custom_name = self._first_string_arg(statement)
            return [ColumnInfo(name=custom_name or "id", data_type="id", nullable=False)]

        if method == "foreignIdFor":
            class_match = re.search(
                r"foreignIdFor\(\s*([A-Za-z0-9_\\]+)::class(?:,\s*'([^']+)')?",
                statement,
            )
            if not class_match:
                return []
            target_class = class_match.group(1).split("\\")[-1]
            column_name = class_match.group(2) or f"{self._snake_case(target_class)}_id"
            return [
                ColumnInfo(
                    name=column_name,
                    data_type="foreignId",
                    nullable="->nullable()" in statement,
                    default=self._extract_default(statement),
                    foreign_table=self._table_from_model_name(target_class),
                    foreign_column="id",
                )
            ]

        if method == "foreign":
            column_name = self._first_string_arg(statement)
            if not column_name:
                return []
            foreign_column, foreign_table = self._extract_explicit_foreign(statement)
            return [
                ColumnInfo(
                    name=column_name,
                    data_type="foreign",
                    foreign_table=foreign_table,
                    foreign_column=foreign_column or "id",
                )
            ]

        column_name = self._first_string_arg(statement)
        if not column_name:
            return []

        column = ColumnInfo(
            name=column_name,
            data_type=method,
            nullable="->nullable()" in statement,
            default=self._extract_default(statement),
            length=self._extract_length(statement, method),
        )

        if method.startswith("foreignId") or column_name.endswith("_id"):
            constrained = re.search(
                r"->constrained\(\s*'([^']+)'(?:,\s*'([^']+)')?\s*\)",
                statement,
            )
            if constrained:
                column.foreign_table = constrained.group(1)
                column.foreign_column = constrained.group(2) or "id"
            elif "->constrained()" in statement:
                column.foreign_table = self._infer_foreign_table(column_name)
            else:
                foreign_column, foreign_table = self._extract_explicit_foreign(statement)
                if foreign_table:
                    column.foreign_table = foreign_table
                    column.foreign_column = foreign_column or "id"
                else:
                    column.foreign_table = self._infer_foreign_table(column_name)
                    column.foreign_column = "id"

        return [column]

    @staticmethod
    def _first_string_arg(statement: str) -> str | None:
        match = re.search(r"\(\s*'([^']+)'", statement)
        return match.group(1) if match else None

    @staticmethod
    def _extract_default(statement: str) -> str | None:
        match = re.search(r"->default\(([^)]+)\)", statement)
        return match.group(1).strip() if match else None

    @staticmethod
    def _extract_explicit_foreign(statement: str) -> tuple[str | None, str | None]:
        references = re.search(r"->references\(\s*'([^']+)'\s*\)", statement)
        on_table = re.search(r"->on\(\s*'([^']+)'\s*\)", statement)
        return (
            references.group(1) if references else None,
            on_table.group(1) if on_table else None,
        )

    @staticmethod
    def _extract_length(statement: str, method: str) -> int | None:
        if method not in {"string", "char", "decimal"}:
            return None
        match = re.search(r"\(\s*'[^']+'\s*,\s*(\d+)", statement)
        return int(match.group(1)) if match else None

    def _build_field_specs(self, model: ModelInfo) -> list[FieldSpec]:
        columns = self._schema_by_table.get(model.table_name, {})
        if columns:
            fields: list[FieldSpec] = []
            for col in columns.values():
                if col.name == "id" or col.name in AUDIT_COLUMNS:
                    continue
                fields.append(
                    FieldSpec(
                        name=col.name,
                        data_type=col.data_type,
                        nullable=col.nullable,
                        required=not col.nullable and col.default is None,
                        length=col.length,
                        foreign_table=col.foreign_table,
                        foreign_column=col.foreign_column,
                    )
                )
            if fields:
                return sorted(fields, key=lambda item: item.name)

        fallback_fields: list[FieldSpec] = []
        for name in model.fillable:
            if name == "id" or name in AUDIT_COLUMNS:
                continue
            fallback_fields.append(
                FieldSpec(
                    name=name,
                    data_type="string",
                    nullable=True,
                    required=False,
                )
            )
        return fallback_fields

    def _append_model_relations(
        self,
        *,
        targets: list[ModelInfo],
        model_by_name: dict[str, ModelInfo],
        model_by_table: dict[str, ModelInfo],
    ) -> dict[str, list[str]]:
        updates: dict[str, list[str]] = {}
        pending_methods: dict[str, list[str]] = {}
        needs_belongs: set[str] = set()
        needs_has_many: set[str] = set()

        for model in targets:
            columns = self._schema_by_table.get(model.table_name, {})
            for col in columns.values():
                if not col.name.endswith("_id") or col.name == "id":
                    continue
                target_table = col.foreign_table or self._infer_foreign_table(col.name)
                if not target_table:
                    continue
                target_model = model_by_table.get(target_table)
                if not target_model or target_model.class_name == model.class_name:
                    continue

                belongs_name = self._camel_case(col.name[:-3])
                if belongs_name not in model.methods:
                    method_text = self._render_belongs_to_method(
                        method_name=belongs_name,
                        target_model=target_model.class_name,
                        foreign_key=col.name,
                    )
                    pending_methods.setdefault(model.class_name, []).append(method_text)
                    model.methods.add(belongs_name)
                    needs_belongs.add(model.class_name)
                    updates.setdefault(model.class_name, []).append(belongs_name)

                parent_method = self._camel_case(
                    self._pluralize(self._snake_case(model.class_name))
                )
                if parent_method not in target_model.methods:
                    method_text = self._render_has_many_method(
                        method_name=parent_method,
                        target_model=model.class_name,
                        foreign_key=col.name,
                    )
                    pending_methods.setdefault(target_model.class_name, []).append(method_text)
                    target_model.methods.add(parent_method)
                    needs_has_many.add(target_model.class_name)
                    updates.setdefault(target_model.class_name, []).append(parent_method)

        for class_name, methods in pending_methods.items():
            model = model_by_name.get(class_name)
            if model is None:
                continue
            text = model.path.read_text(encoding="utf-8")
            if class_name in needs_belongs:
                text = self._ensure_import(
                    text, "use Illuminate\\Database\\Eloquent\\Relations\\BelongsTo;"
                )
            if class_name in needs_has_many:
                text = self._ensure_import(
                    text, "use Illuminate\\Database\\Eloquent\\Relations\\HasMany;"
                )
            text = self._append_methods_to_class(text, methods)
            model.path.write_text(text, encoding="utf-8")

        return updates

    @staticmethod
    def _ensure_import(text: str, use_statement: str) -> str:
        if use_statement in text:
            return text

        lines = text.splitlines()
        use_indexes = [idx for idx, line in enumerate(lines) if line.startswith("use ")]
        if use_indexes:
            insert_at = use_indexes[-1] + 1
            lines.insert(insert_at, use_statement)
        else:
            namespace_index = next(
                (idx for idx, line in enumerate(lines) if line.startswith("namespace ")),
                None,
            )
            if namespace_index is None:
                return text
            lines.insert(namespace_index + 1, "")
            lines.insert(namespace_index + 2, use_statement)

        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def _append_methods_to_class(text: str, methods: list[str]) -> str:
        class_end = text.rfind("}")
        if class_end == -1:
            return text

        rendered = "\n\n".join(methods)
        head = text[:class_end].rstrip()
        tail = text[class_end:]
        return f"{head}\n\n{rendered}\n{tail.lstrip()}"

    @staticmethod
    def _render_belongs_to_method(method_name: str, target_model: str, foreign_key: str) -> str:
        return (
            f"    public function {method_name}(): BelongsTo\n"
            "    {\n"
            f"        return $this->belongsTo({target_model}::class, '{foreign_key}');\n"
            "    }"
        )

    @staticmethod
    def _render_has_many_method(method_name: str, target_model: str, foreign_key: str) -> str:
        return (
            f"    public function {method_name}(): HasMany\n"
            "    {\n"
            f"        return $this->hasMany({target_model}::class, '{foreign_key}');\n"
            "    }"
        )

    def _render_controller(self, model: ModelInfo) -> str:
        name = model.class_name
        return f"""<?php

namespace App\\Http\\Controllers;

use App\\Http\\Requests\\{name}\\Save{name}Request;
use App\\Http\\Requests\\{name}\\Search{name}Request;
use App\\Services\\{name}Service;
use Illuminate\\Http\\JsonResponse;

class {name}Controller extends Controller
{{
    public function __construct(private readonly {name}Service $service)
    {{
    }}

    public function index(Search{name}Request $request): JsonResponse
    {{
        $result = $this->service->search($request->validated());
        return response()->json($result);
    }}

    public function store(Save{name}Request $request): JsonResponse
    {{
        $created = $this->service->create($request->validated());
        return response()->json($created, 201);
    }}

    public function show($id): JsonResponse
    {{
        $item = $this->service->findById($id);
        return response()->json($item);
    }}

    public function update(Save{name}Request $request, $id): JsonResponse
    {{
        $updated = $this->service->update($id, $request->validated());
        return response()->json($updated);
    }}

    public function destroy($id): JsonResponse
    {{
        $this->service->delete($id);
        return response()->json(null, 204);
    }}
}}
"""

    def _render_service(self, model: ModelInfo) -> str:
        name = model.class_name
        return f"""<?php

namespace App\\Services;

use App\\Models\\{name};
use App\\Repositories\\{name}Repository;
use Illuminate\\Contracts\\Pagination\\LengthAwarePaginator;

class {name}Service
{{
    public function __construct(private readonly {name}Repository $repository)
    {{
    }}

    public function search(array $conditions): LengthAwarePaginator
    {{
        return $this->repository->search($conditions);
    }}

    public function findById($id): {name}
    {{
        return $this->repository->findById($id);
    }}

    public function create(array $data): {name}
    {{
        return $this->repository->create($data);
    }}

    public function update($id, array $data): {name}
    {{
        return $this->repository->update($id, $data);
    }}

    public function delete($id): bool
    {{
        return $this->repository->delete($id);
    }}
}}
"""

    def _render_repository(self, model: ModelInfo, fields: list[FieldSpec]) -> str:
        name = model.class_name
        sortable = ["id"] + [field.name for field in fields]
        sortable_values = ", ".join(f"'{value}'" for value in sorted(set(sortable)))
        default_sort = "created_at"
        table_columns = self._schema_by_table.get(model.table_name, {})
        if "created_at" not in table_columns:
            default_sort = "id"

        where_lines: list[str] = []
        for field in fields:
            condition = self._render_search_condition(field)
            if condition:
                where_lines.append(condition)
        where_body = "\n".join(where_lines) if where_lines else "        // no searchable fields inferred"

        return f"""<?php

namespace App\\Repositories;

use App\\Models\\{name};
use Illuminate\\Contracts\\Pagination\\LengthAwarePaginator;

class {name}Repository
{{
    public function search(array $conditions): LengthAwarePaginator
    {{
        $query = {name}::query();

{where_body}

        $allowedSort = [{sortable_values}];
        $sort = $conditions['sort'] ?? '{default_sort}';
        if (!in_array($sort, $allowedSort, true)) {{
            $sort = '{default_sort}';
        }}

        $direction = strtolower((string) ($conditions['direction'] ?? 'desc'));
        if (!in_array($direction, ['asc', 'desc'], true)) {{
            $direction = 'desc';
        }}

        $perPage = (int) ($conditions['per_page'] ?? 15);
        if ($perPage < 1) {{
            $perPage = 15;
        }}
        if ($perPage > 100) {{
            $perPage = 100;
        }}

        return $query->orderBy($sort, $direction)->paginate($perPage);
    }}

    public function findById($id): {name}
    {{
        return {name}::query()->findOrFail($id);
    }}

    public function create(array $data): {name}
    {{
        return {name}::query()->create($data);
    }}

    public function update($id, array $data): {name}
    {{
        $model = $this->findById($id);
        $model->fill($data);
        $model->save();

        return $model;
    }}

    public function delete($id): bool
    {{
        $model = $this->findById($id);
        return (bool) $model->delete();
    }}
}}
"""

    def _render_save_request(self, model: ModelInfo, fields: list[FieldSpec]) -> str:
        rules = []
        for field in fields:
            rule_tokens: list[str] = []
            if field.nullable:
                rule_tokens.append("'nullable'")
            else:
                rule_tokens.append("$requiredRule")
            rule_tokens.extend(self._save_rule_tokens(field))
            tokens = ", ".join(rule_tokens)
            rules.append(f"            '{field.name}' => [{tokens}],")

        rules_text = "\n".join(rules) if rules else "            // No writable columns inferred."

        name = model.class_name
        return f"""<?php

namespace App\\Http\\Requests\\{name};

use Illuminate\\Foundation\\Http\\FormRequest;

class Save{name}Request extends FormRequest
{{
    public function authorize(): bool
    {{
        return true;
    }}

    public function rules(): array
    {{
        $requiredRule = $this->isMethod('post') ? 'required' : 'sometimes';

        return [
{rules_text}
        ];
    }}
}}
"""

    def _render_search_request(self, model: ModelInfo, fields: list[FieldSpec]) -> str:
        rules = []
        sortable = ["id"] + [field.name for field in fields]
        sort_rule = "in:" + ",".join(sorted(set(sortable)))

        for field in fields:
            tokens = ["'nullable'"] + self._search_rule_tokens(field)
            rules.append(f"            '{field.name}' => [{', '.join(tokens)}],")

        rules.extend(
            [
                "            'per_page' => ['nullable', 'integer', 'min:1', 'max:100'],",
                f"            'sort' => ['nullable', 'string', '{sort_rule}'],",
                "            'direction' => ['nullable', 'in:asc,desc'],",
            ]
        )

        name = model.class_name
        return f"""<?php

namespace App\\Http\\Requests\\{name};

use Illuminate\\Foundation\\Http\\FormRequest;

class Search{name}Request extends FormRequest
{{
    public function authorize(): bool
    {{
        return true;
    }}

    public function rules(): array
    {{
        return [
{chr(10).join(rules)}
        ];
    }}
}}
"""

    @staticmethod
    def _render_search_condition(field: FieldSpec) -> str:
        key = field.name
        if field.data_type.lower() in {"string", "char", "text", "mediumtext", "longtext"}:
            return (
                f"        if (isset($conditions['{key}']) && $conditions['{key}'] !== '') {{\n"
                f"            $query->where('{key}', 'like', '%' . $conditions['{key}'] . '%');\n"
                "        }"
            )
        if field.data_type.lower() in {"date", "datetime", "timestamp"}:
            return (
                f"        if (isset($conditions['{key}']) && $conditions['{key}'] !== '') {{\n"
                f"            $query->whereDate('{key}', $conditions['{key}']);\n"
                "        }"
            )
        return (
            f"        if (array_key_exists('{key}', $conditions) && $conditions['{key}'] !== null && $conditions['{key}'] !== '') {{\n"
            f"            $query->where('{key}', $conditions['{key}']);\n"
            "        }"
        )

    @staticmethod
    def _save_rule_tokens(field: FieldSpec) -> list[str]:
        tokens = BackendStackGenerator._base_type_rule_tokens(field)
        if field.length and field.data_type.lower() in {"string", "char"}:
            tokens.append(f"'max:{field.length}'")
        if field.name.endswith("_id") and field.foreign_table:
            tokens.append(f"'exists:{field.foreign_table},{field.foreign_column}'")
        return tokens

    @staticmethod
    def _search_rule_tokens(field: FieldSpec) -> list[str]:
        base = BackendStackGenerator._base_type_rule_tokens(field)
        # search is always optional; we intentionally skip exists checks here
        return base

    @staticmethod
    def _base_type_rule_tokens(field: FieldSpec) -> list[str]:
        data_type = field.data_type.lower()
        if field.name.endswith("_id"):
            return ["'integer'"]
        if data_type in {"integer", "tinyinteger", "smallinteger", "mediuminteger", "biginteger", "foreignid"}:
            return ["'integer'"]
        if data_type in {"decimal", "numeric", "double", "float"}:
            return ["'numeric'"]
        if data_type in {"boolean", "bool"}:
            return ["'boolean'"]
        if data_type in {"date", "datetime", "timestamp"}:
            return ["'date'"]
        if data_type in {"json"}:
            return ["'array'"]
        if data_type in {"text", "mediumtext", "longtext"}:
            return ["'string'"]
        return ["'string'"]

    @staticmethod
    def _extract_table_name(text: str) -> str | None:
        match = re.search(r"protected\s+\$table\s*=\s*'([^']+)';", text)
        return match.group(1) if match else None

    @staticmethod
    def _extract_fillable(text: str) -> list[str]:
        match = re.search(r"protected\s+\$fillable\s*=\s*\[(.*?)\];", text, re.DOTALL)
        if not match:
            return []
        return re.findall(r"'([^']+)'", match.group(1))

    @staticmethod
    def _infer_foreign_table(column_name: str) -> str | None:
        if not column_name.endswith("_id"):
            return None
        base = column_name[:-3]
        if not base:
            return None
        return BackendStackGenerator._pluralize(base)

    @staticmethod
    def _table_from_model_name(model_name: str) -> str:
        return BackendStackGenerator._pluralize(BackendStackGenerator._snake_case(model_name))

    @staticmethod
    def _snake_case(value: str) -> str:
        value = re.sub(r"(?<!^)([A-Z])", r"_\1", value).lower()
        value = re.sub(r"[^a-z0-9_]", "", value)
        return re.sub(r"_+", "_", value).strip("_")

    @staticmethod
    def _camel_case(value: str) -> str:
        parts = [part for part in value.split("_") if part]
        if not parts:
            return value
        return parts[0] + "".join(part.capitalize() for part in parts[1:])

    @staticmethod
    def _pluralize(word: str) -> str:
        if word.endswith("ies"):
            return word
        if word.endswith("y") and len(word) > 1:
            return f"{word[:-1]}ies"
        if word.endswith("s"):
            return word
        return f"{word}s"

