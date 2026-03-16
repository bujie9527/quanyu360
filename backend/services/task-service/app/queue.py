from __future__ import annotations

import json
from uuid import UUID

from redis import Redis

from app.config import settings


def get_redis_client() -> Redis:
    if not settings.redis_url:
        raise RuntimeError("REDIS_URL is not configured for task-service.")
    return Redis.from_url(settings.redis_url, decode_responses=True)


def enqueue_task(task_id: UUID) -> None:
    payload = json.dumps({"task_id": str(task_id)})
    client = get_redis_client()
    client.rpush(settings.task_queue_name, payload)


def dequeue_task(block_seconds: int | None = None) -> UUID | None:
    client = get_redis_client()
    result = client.blpop(settings.task_queue_name, timeout=block_seconds or settings.task_worker_block_seconds)
    if result is None:
        return None
    _, payload = result
    item = json.loads(payload)
    return UUID(item["task_id"])
