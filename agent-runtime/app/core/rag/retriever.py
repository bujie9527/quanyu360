"""Retriever: vector search over knowledge base documents."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import get_settings


@dataclass
class RetrievedChunk:
    """A single retrieved document chunk."""
    id: str
    content: str
    score: float
    document_id: str | None = None
    chunk_index: int | None = None


class Retriever(Protocol):
    """Protocol for vector search retrieval."""

    def retrieve(
        self,
        query: str,
        knowledge_base_id: str,
        project_id: str,
        limit: int = 10,
    ) -> list[RetrievedChunk]:
        """Retrieve relevant chunks for a query."""
        ...


class ProjectServiceRetriever:
    """Retriever that calls project-service knowledge base search API."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._base_url = self.settings.project_service_url

    def retrieve(
        self,
        query: str,
        knowledge_base_id: str,
        project_id: str,
        limit: int = 10,
    ) -> list[RetrievedChunk]:
        """Retrieve via POST to project-service knowledge base search."""
        if not query.strip():
            return []
        url = f"{self._base_url.rstrip('/')}/api/projects/{project_id}/knowledge-bases/{knowledge_base_id}/search"
        payload = {"query": query, "limit": limit}
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, Exception):
            return []
        results = data.get("results") or []
        return [
            RetrievedChunk(
                id=r.get("id", ""),
                content=r.get("content", ""),
                score=float(r.get("score", 0.0)),
                document_id=r.get("document_id"),
                chunk_index=r.get("chunk_index"),
            )
            for r in results
        ]
