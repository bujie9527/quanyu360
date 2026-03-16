from __future__ import annotations

from datetime import datetime
from datetime import timezone

from redis import Redis

from app.core.config import get_settings
from app.core.schemas import MemoryEntry


class RuntimeMemory:
    def __init__(self, agent_id: str, task_id: str) -> None:
        self.agent_id = agent_id
        self.task_id = task_id
        self.entries: list[MemoryEntry] = []

    def add(self, role: str, content: str, metadata: dict | None = None) -> MemoryEntry:
        entry = MemoryEntry(
            role=role,
            content=content,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {},
        )
        self.entries.append(entry)
        return entry

    def list(self) -> list[MemoryEntry]:
        return list(self.entries)


class RedisMemoryStore:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = Redis.from_url(settings.redis_url, decode_responses=True)
        self._key_prefix = settings.memory_key_prefix

    def save(self, memory: RuntimeMemory) -> None:
        self._client.set(
            f"{self._key_prefix}:{memory.agent_id}:{memory.task_id}",
            "[" + ",".join(entry.model_dump_json() for entry in memory.entries) + "]",
        )
