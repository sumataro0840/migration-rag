def retrieve_related_docs(parsed_request, project_root: str):
    return [
        {
            "file_path": f"database/migrations/example_add_column_to_{parsed_request.table}.php",
            "reason": f"同じ {parsed_request.table} テーブルへのカラム追加事例"
        }
    ]