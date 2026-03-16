"""Short-term memory: Redis-backed conversation storage with TTL."""
from __future__ import annotations

import json
from datetime import datetime
from datetime import timezone
from typing import Any

import structlog

from app.core.config import get_settings
from app.core.schemas import ConversationTurn


class ShortTermMemory:
    """Stores recent conversations in Redis. TTL-based eviction."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = structlog.get_logger(self.settings.service_name).bind(component="short-term-memory")
        self._redis = None

    def _get_client(self):
        if self._redis is None:
            from redis import Redis
            self._redis = Redis.from_url(self.settings.redis_url, decode_responses=True)
        return self._redis

    def _key(self, agent_id: str, task_id: str | None = None) -> str:
        base = f"{self.settings.memory_key_prefix}:short:{agent_id}"
        return f"{base}:{task_id}" if task_id else f"{base}:global"

    def store_conversation(
        self,
        agent_id: str,
        turns: list[ConversationTurn],
        task_id: str | None = None,
    ) -> bool:
        """Append conversation turns to short-term buffer."""
        if not turns:
            return True
        try:
            client = self._get_client()
            key = self._key(agent_id, task_id)
            existing = client.get(key)
            stored: list[dict[str, Any]] = json.loads(existing) if existing else []
            for turn in turns:
                stored.append(turn.model_dump(mode="json"))
            stored = stored[-self.settings.short_term_max_turns:]
            client.setex(
                key,
                self.settings.short_term_ttl_seconds,
                json.dumps(stored, default=str),
            )
            self.logger.info(
                "Stored conversation.",
                agent_id=agent_id,
                task_id=task_id,
                turns_added=len(turns),
                total_turns=len(stored),
                stage="short_term_store",
            )
            return True
        except Exception as exc:
            self.logger.warning(
                "Failed to store short-term memory.",
                agent_id=agent_id,
                task_id=task_id,
                error=str(exc),
                stage="short_term_store",
            )
            return False

    def retrieve_context(
        self,
        agent_id: str,
        task_id: str | None = None,
        limit: int | None = None,
    ) -> list[ConversationTurn]:
        """Retrieve recent conversation turns for context."""
        try:
            client = self._get_client()
            key = self._key(agent_id, task_id)
            raw = client.get(key)
            if not raw:
                return []
            data = json.loads(raw)
            turns = [ConversationTurn.model_validate(item) for item in data]
            n = limit or self.settings.short_term_max_turns
            return turns[-n:]
        except Exception as exc:
            self.logger.warning(
                "Failed to retrieve short-term memory.",
                agent_id=agent_id,
                task_id=task_id,
                error=str(exc),
                stage="short_term_retrieve",
            )
            return []
