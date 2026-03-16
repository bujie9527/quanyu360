"""Long-term memory: Qdrant vector store for semantic retrieval."""
from __future__ import annotations

import uuid
from datetime import datetime
from datetime import timezone
from typing import Any

import structlog

from app.core.config import get_settings


class LongTermMemory:
    """Stores and retrieves memories in Qdrant. Semantic search via embeddings."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = structlog.get_logger(self.settings.service_name).bind(component="long-term-memory")
        self._client = None
        self._available = True  # Assume available until first failure

    def _get_client(self):
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
                self._client = QdrantClient(url=self.settings.qdrant_url)
            except Exception as exc:
                self.logger.warning(
                    "Qdrant client init failed, long-term memory disabled.",
                    error=str(exc),
                    stage="long_term_init",
                )
                self._available = False
                return None
        return self._client

    def store_memories(
        self,
        agent_id: str,
        documents: list[str],
        metadata: list[dict[str, Any]] | None = None,
        task_id: str | None = None,
    ) -> list[str]:
        """Store memory documents with embeddings. Returns created IDs."""
        if not documents:
            return []
        client = self._get_client()
        if not client:
            return []
        try:
            meta_list = metadata or [{}] * len(documents)
            if len(meta_list) != len(documents):
                meta_list = [{}] * len(documents)

            payloads = [
                {
                    "agent_id": agent_id,
                    "task_id": task_id or "",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **m,
                }
                for m in meta_list
            ]

            ids = [str(uuid.uuid4()) for _ in documents]
            client.add(
                collection_name=self.settings.qdrant_collection,
                documents=documents,
                metadata=payloads,
                ids=ids,
            )
            self.logger.info(
                "Stored long-term memories.",
                agent_id=agent_id,
                task_id=task_id,
                count=len(documents),
                stage="long_term_store",
            )
            return ids
        except Exception as exc:
            self.logger.warning(
                "Failed to store long-term memory.",
                agent_id=agent_id,
                task_id=task_id,
                error=str(exc),
                stage="long_term_store",
            )
            return []

    def retrieve_context(
        self,
        agent_id: str,
        query: str,
        limit: int | None = None,
        task_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant memories by semantic similarity to query."""
        client = self._get_client()
        if not client:
            return []
        try:
            from qdrant_client.http import models as qdrant_models

            n = limit or self.settings.long_term_retrieve_limit
            must = [qdrant_models.FieldCondition(key="agent_id", match=qdrant_models.MatchValue(value=agent_id))]
            if task_id:
                must.append(
                    qdrant_models.FieldCondition(key="task_id", match=qdrant_models.MatchValue(value=task_id))
                )

            results = client.query(
                collection_name=self.settings.qdrant_collection,
                query_text=query,
                query_filter=qdrant_models.Filter(must=must),
                limit=n,
            )
            out: list[dict[str, Any]] = []
            for r in results:
                content = getattr(r, "document", None) or (r.metadata or {}).get("document", "")
                out.append({
                    "id": str(getattr(r, "id", "")),
                    "content": content,
                    "metadata": r.metadata or {},
                    "score": getattr(r, "score", 0.0),
                })
            return out
        except Exception as exc:
            self.logger.warning(
                "Failed to retrieve long-term memory.",
                agent_id=agent_id,
                query=query[:50],
                error=str(exc),
                stage="long_term_retrieve",
            )
            return []
