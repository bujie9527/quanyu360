from __future__ import annotations

import json
from redis import Redis

from app.core.config import get_settings


def get_redis_client() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


def enqueue_execution(execution_id: str) -> None:
    settings = get_settings()
    get_redis_client().rpush(settings.execution_queue_name, json.dumps({"execution_id": execution_id}))


def dequeue_execution() -> str | None:
    settings = get_settings()
    result = get_redis_client().blpop(settings.execution_queue_name, timeout=settings.execution_worker_block_seconds)
    if result is None:
        return None
    _, payload = result
    data = json.loads(payload)
    return data["execution_id"]
