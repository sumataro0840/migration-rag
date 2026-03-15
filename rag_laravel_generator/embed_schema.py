"""Embed table schema documents with OpenAI embeddings."""

from __future__ import annotations

from typing import Any
import os

from openai import OpenAI


DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


def _get_client(openai_api_key: str | None = None) -> OpenAI:
    """OpenAI クライアントを生成する。"""
    api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY が設定されていません。")
    return OpenAI(api_key=api_key)


def create_embedding(text: str, *, openai_api_key: str | None = None) -> list[float]:
    """Create a single embedding vector for text."""
    client = _get_client(openai_api_key)
    # 旧API: openai.Embedding.create(...) は openai>=1.0.0 で廃止済み
    response = client.embeddings.create(
        model=DEFAULT_EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


def embed_documents(documents: list[dict[str, Any]], *, openai_api_key: str | None = None) -> list[list[float]]:
    """Embed a list of docs with keys 'id' and 'schema_text'."""
    embeddings: list[list[float]] = []
    for doc in documents:
        vector = create_embedding(doc["schema_text"], openai_api_key=openai_api_key)
        embeddings.append(vector)
    return embeddings