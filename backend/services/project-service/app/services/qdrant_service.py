"""Qdrant vector store for knowledge base embeddings."""
from __future__ import annotations

import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from app.config import settings

VECTOR_SIZE = 1536  # text-embedding-3-small


class QdrantKnowledgeStore:
    """Qdrant-backed vector store per knowledge base. One collection per KB."""

    def __init__(self) -> None:
        self._client: QdrantClient | None = None

    def _get_client(self) -> QdrantClient | None:
        if not settings.qdrant_url:
            return None
        if self._client is None:
            self._client = QdrantClient(url=settings.qdrant_url)
        return self._client

    def _collection_name(self, knowledge_base_id: str) -> str:
        return f"kb_{knowledge_base_id.replace('-', '_')}"

    def ensure_collection(self, knowledge_base_id: str) -> bool:
        """Create collection if not exists."""
        client = self._get_client()
        if not client:
            return False
        name = self._collection_name(knowledge_base_id)
        try:
            collections = client.get_collections().collections
            if any(c.name == name for c in collections):
                return True
            client.create_collection(
                collection_name=name,
                vectors_config=qdrant_models.VectorParams(size=VECTOR_SIZE, distance=qdrant_models.Distance.COSINE),
            )
            return True
        except Exception:
            return False

    def upsert(
        self,
        knowledge_base_id: str,
        point_ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> bool:
        """Upsert vectors with payloads."""
        client = self._get_client()
        if not client or not point_ids or len(point_ids) != len(vectors) != len(payloads):
            return False
        name = self._collection_name(knowledge_base_id)
        points = [
            qdrant_models.PointStruct(id=pid, vector=v, payload=p)
            for pid, v, p in zip(point_ids, vectors, payloads)
        ]
        try:
            client.upsert(collection_name=name, points=points)
            return True
        except Exception:
            return False

    def search(
        self,
        knowledge_base_id: str,
        query_vector: list[float],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search by vector. Returns list of {id, score, payload}."""
        client = self._get_client()
        if not client:
            return []
        name = self._collection_name(knowledge_base_id)
        try:
            results = client.search(
                collection_name=name,
                query_vector=query_vector,
                limit=limit,
            )
            return [
                {"id": str(r.id), "score": r.score or 0.0, "payload": r.payload or {}}
                for r in results
            ]
        except Exception:
            return []

    def delete_by_ids(self, knowledge_base_id: str, point_ids: list[str]) -> bool:
        """Remove points by ID."""
        client = self._get_client()
        if not client or not point_ids:
            return True
        name = self._collection_name(knowledge_base_id)
        try:
            client.delete(collection_name=name, points_selector=point_ids)
            return True
        except Exception:
            return False
