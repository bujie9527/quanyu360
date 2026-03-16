"""Unified memory management: in-session memory and persistent store."""
from __future__ import annotations

import json
from datetime import datetime
from datetime import timezone

import structlog

from app.core.config import get_settings
from app.core.memory import RuntimeMemory
from app.core.schemas import ExecutionLogEntry
from app.core.schemas import MemoryEntry


class MemoryManager:
    """Manages agent memory: session creation, persistence, and retrieval."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = structlog.get_logger(self.settings.service_name).bind(component="memory-manager")
        self._redis = None

    def _get_client(self):
        if self._redis is None:
            from redis import Redis
            self._redis = Redis.from_url(self.settings.redis_url, decode_responses=True)
        return self._redis

    def create_session(self, agent_id: str, task_id: str) -> RuntimeMemory:
        """Create a new in-session memory for an agent run."""
        return RuntimeMemory(agent_id=agent_id, task_id=task_id)

    def persist(
        self,
        memory: RuntimeMemory,
        logs: list[ExecutionLogEntry] | None = None,
    ) -> bool:
        """Persist memory to Redis. Returns True on success."""
        started_at = datetime.now(timezone.utc)
        try:
            client = self._get_client()
            key = f"{self.settings.memory_key_prefix}:{memory.agent_id}:{memory.task_id}"
            payload = json.dumps([e.model_dump(mode="json") for e in memory.entries], default=str)
            client.set(key, payload)

            duration_ms = (datetime.now(timezone.utc) - started_at).total_seconds() * 1000
            self.logger.info(
                "Memory persisted.",
                agent_id=memory.agent_id,
                task_id=memory.task_id,
                entries_count=len(memory.entries),
                duration_ms=round(duration_ms, 2),
                stage="memory_persist",
            )
            if logs is not None:
                logs.append(
                    ExecutionLogEntry(
                        stage="memory_persist",
                        level="info",
                        message="Execution memory persisted.",
                        timestamp=datetime.now(timezone.utc),
                        details={"entries": len(memory.entries), "duration_ms": round(duration_ms, 2)},
                    )
                )
            return True
        except Exception as exc:
            self.logger.warning(
                "Failed to persist execution memory.",
                agent_id=memory.agent_id,
                task_id=memory.task_id,
                error=str(exc),
                stage="memory_persist",
            )
            if logs is not None:
                logs.append(
                    ExecutionLogEntry(
                        stage="memory_persist",
                        level="warning",
                        message="Failed to persist execution memory.",
                        timestamp=datetime.now(timezone.utc),
                        details={"error": str(exc)},
                    )
                )
            return False

    def load(self, agent_id: str, task_id: str) -> list[MemoryEntry] | None:
        """Load previously persisted memory. Returns None if not found or error."""
        try:
            client = self._get_client()
            key = f"{self.settings.memory_key_prefix}:{agent_id}:{task_id}"
            raw = client.get(key)
            if not raw:
                return None
            data = json.loads(raw)
            return [MemoryEntry.model_validate(item) for item in data]
        except Exception as exc:
            self.logger.warning(
                "Failed to load memory.",
                agent_id=agent_id,
                task_id=task_id,
                error=str(exc),
                stage="memory_load",
            )
            return None
