"""RAG pipeline helpers for Laravel migration generation."""
from .ingest_excel import ingest_schemas_from_excel, table_schema_to_document, table_schema_to_text
from .backend_stack_generator import BackendStackGenerator, GenerationReport

try:
    from .vector_store import VectorStore
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    VectorStore = None  # type: ignore[assignment]

try:
    from .embed_schema import create_embedding, embed_documents
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    create_embedding = None  # type: ignore[assignment]
    embed_documents = None  # type: ignore[assignment]

__all__ = [
    "ingest_schemas_from_excel",
    "table_schema_to_document",
    "table_schema_to_text",   # 後方互換エイリアス
    "VectorStore",
    "create_embedding",
    "embed_documents",
    "BackendStackGenerator",
    "GenerationReport",
]
