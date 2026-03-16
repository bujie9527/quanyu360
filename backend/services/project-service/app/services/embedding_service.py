"""OpenAI embedding service for knowledge base documents."""
from __future__ import annotations

from openai import OpenAI

from app.config import settings

DEFAULT_MODEL = "text-embedding-3-small"


class EmbeddingService:
    """Generates embeddings via OpenAI API."""

    def __init__(self) -> None:
        self._client: OpenAI | None = None

    def _get_client(self) -> OpenAI | None:
        if not settings.openai_api_key:
            return None
        if self._client is None:
            self._client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )
        return self._client

    def embed(self, texts: list[str], model: str = DEFAULT_MODEL) -> list[list[float]]:
        """Embed a list of texts. Returns list of vectors. Empty if API unavailable."""
        client = self._get_client()
        if not client or not texts:
            return []
        resp = client.embeddings.create(input=texts, model=model)
        return [d.embedding for d in resp.data]
