"""ContextBuilder: format retrieved chunks into prompt context."""
from __future__ import annotations

from app.core.rag.retriever import RetrievedChunk

DEFAULT_MAX_CHARS = 6000


class ContextBuilder:
    """Builds prompt context from retrieved chunks."""

    def __init__(self, max_chars: int = DEFAULT_MAX_CHARS, separator: str = "\n\n---\n\n") -> None:
        self.max_chars = max_chars
        self.separator = separator

    def build(self, chunks: list[RetrievedChunk]) -> str:
        """Format retrieved chunks into a single context string."""
        if not chunks:
            return ""
        parts: list[str] = []
        total = 0
        for i, c in enumerate(chunks):
            content = (c.content or "").strip()
            if not content:
                continue
            part_len = len(content) + (len(self.separator) if parts else 0)
            if total + part_len > self.max_chars and parts:
                break
            prefix = f"[{i + 1}]" if len(chunks) > 1 else ""
            parts.append(f"{prefix} {content}".strip())
            total += part_len
        return self.separator.join(parts) if parts else ""
