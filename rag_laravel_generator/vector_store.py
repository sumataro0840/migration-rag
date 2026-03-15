"""Chroma vector store for schema retrieval."""

from __future__ import annotations

from typing import Any
from pathlib import Path
import os

import chromadb


class VectorStoreError(Exception):
    pass


class VectorStore:
    """Vector storage wrapper around ChromaDB."""

    def __init__(self, persist_directory: str = "./rag_store") -> None:
        self._persist_directory = str(persist_directory)
        # chromadb >= 0.4.x では PersistentClient を使う
        # 旧API: chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", ...)) は廃止済み
        self._client = chromadb.PersistentClient(path=self._persist_directory)
        self._collection = self._client.get_or_create_collection(name="table_schemas")

    def is_empty(self) -> bool:
        return self._collection.count() == 0

    def add_documents(self, docs: list[dict[str, Any]], vectors: list[list[float]]) -> None:
        if len(docs) != len(vectors):
            raise VectorStoreError("docs and vectors length mismatch")

        ids = [doc["id"] for doc in docs]
        metadata = [doc["metadata"] for doc in docs]
        documents = [doc["schema_text"] for doc in docs]

        self._collection.add(
            ids=ids,
            metadatas=metadata,
            documents=documents,
            embeddings=vectors,
        )
        # PersistentClient は自動永続化のため persist() 呼び出し不要

    def query(self, query_embedding: list[float], n_results: int = 1) -> list[dict[str, Any]]:
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["metadatas", "documents", "distances"],
        )
        if not results or not results.get("ids"):
            return []

        entries = []
        for idx in range(len(results["ids"][0])):
            entries.append(
                {
                    "id": results["ids"][0][idx],
                    "metadata": results["metadatas"][0][idx],
                    "schema_text": results["documents"][0][idx],
                    "distance": results["distances"][0][idx],
                }
            )
        return entries