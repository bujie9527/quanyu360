from __future__ import annotations

import json

from app.core.config import get_settings
from app.core.queue import get_redis_client
from app.core.schemas import WorkflowExecutionState
from app.core.schemas import WorkflowExecutionSummary


def _execution_key(execution_id: str) -> str:
    settings = get_settings()
    return f"{settings.execution_state_prefix}:{execution_id}"


def save_execution_state(state: WorkflowExecutionState) -> None:
    settings = get_settings()
    client = get_redis_client()
    client.set(_execution_key(state.execution_id), state.model_dump_json())
    client.sadd(settings.execution_index_key, state.execution_id)


def load_execution_state(execution_id: str) -> WorkflowExecutionState | None:
    payload = get_redis_client().get(_execution_key(execution_id))
    if payload is None:
        return None
    return WorkflowExecutionState.model_validate_json(payload)


def list_execution_summaries() -> list[WorkflowExecutionSummary]:
    settings = get_settings()
    client = get_redis_client()
    execution_ids = sorted(client.smembers(settings.execution_index_key))
    summaries: list[WorkflowExecutionSummary] = []
    for execution_id in execution_ids:
        state = load_execution_state(execution_id)
        if state is None:
            continue
        summaries.append(
            WorkflowExecutionSummary(
                execution_id=state.execution_id,
                workflow_id=state.workflow_id,
                status=state.status,
                current_step=state.current_step,
                started_at=state.started_at,
                completed_at=state.completed_at,
            )
        )
    return sorted(summaries, key=lambda item: item.started_at, reverse=True)
