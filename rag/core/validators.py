def validate_request(req, schema_info):
    warnings = []

    tables = schema_info.get("tables", {})
    if req.table not in tables:
        warnings.append(f"table '{req.table}' が既存スキーマに見つかりません")

    existing_cols = set(tables.get(req.table, []))
    for col in req.columns:
        if col.name in existing_cols:
            warnings.append(f"column '{col.name}' は既に存在する可能性があります")

    if req.operation == "add_column" and not req.need_down:
        warnings.append("down() が未指定です。rollback 方針を確認してください")

    return warnings