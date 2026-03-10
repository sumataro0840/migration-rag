from pathlib import Path
from ingest.parse_migrations import parse_migration_file

def collect_documents(project_root: str):
    docs = []
    migration_dir = Path(project_root) / "database" / "migrations"

    for file in migration_dir.glob("*.php"):
        docs.append(parse_migration_file(str(file)))

    return docs

if __name__ == "__main__":
    docs = collect_documents("..")
    print(docs[:3])