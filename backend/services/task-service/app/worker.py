from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone

import httpx

from app.config import settings
from common.app.core.logging import EVENT_ERROR
from common.app.core.logging import EVENT_TASK_FINISH
from common.app.core.logging import EVENT_TASK_START
from common.app.core.logging import configure_logging
from common.app.core.logging import log_event
from app.config import session_factory
from app.queue import dequeue_task
from app.repositories import TaskRepository
from app.services import TaskService
from common.app.models import Task
from common.app.models import TaskStatus
from common.app.services.tool_permission_service import get_allowed_tool_slugs


@dataclass
class TaskExecutionResult:
    success: bool
    payload: dict[str, object]
    error_message: str | None = None


def _call_team_runtime(task: Task) -> TaskExecutionResult:
    """Invoke agent-runtime team execution for tasks with team_id."""
    if task.team is None or not task.team.members:
        return TaskExecutionResult(
            success=False,
            payload={},
            error_message="Team not loaded or has no members.",
        )
    base_url = (settings.agent_runtime_url or "").rstrip("/")
    if not base_url:
        return TaskExecutionResult(
            success=False,
            payload={},
            error_message="AGENT_RUNTIME_URL is not configured.",
        )
    tenant_id = str(task.project.tenant_id) if task.project else None
    members = [
        {
            "agent_id": str(m.agent_id),
            "role_in_team": m.role_in_team,
            "order_index": m.order_index,
            "model": m.agent.model if m.agent else None,
        }
        for m in sorted(task.team.members, key=lambda x: (x.order_index, str(x.agent_id)))
    ]
    payload_body = {
        "team_id": str(task.team_id),
        "task_id": str(task.id),
        "execution_type": task.team.execution_type.value,
        "members": members,
        "task": {
            "title": task.title,
            "description": task.description,
            "input_payload": task.input_payload or {},
        },
        "metadata": {
            "tenant_id": tenant_id,
            "project_id": str(task.project_id),
            "workflow_id": str(task.workflow_id) if task.workflow_id else None,
        },
    }
    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(
                f"{base_url}/api/v1/teams/runs",
                json=payload_body,
                headers={"Content-Type": "application/json"},
            )
    except httpx.ConnectError as e:
        return TaskExecutionResult(
            success=False,
            payload={},
            error_message=f"Agent runtime connection failed: {e!s}",
        )
    except httpx.TimeoutException as e:
        return TaskExecutionResult(
            success=False,
            payload={},
            error_message=f"Agent runtime timeout: {e!s}",
        )
    except Exception as e:
        return TaskExecutionResult(
            success=False,
            payload={},
            error_message=f"Agent runtime error: {e!s}",
        )
    if resp.status_code >= 400:
        err_text = resp.text[:500] if resp.text else ""
        return TaskExecutionResult(
            success=False,
            payload={},
            error_message=f"Agent runtime returned {resp.status_code}: {err_text}",
        )
    data = resp.json()
    status_val = data.get("status", "unknown")
    combined = data.get("combined_result", {})
    member_results = data.get("member_results", [])
    logs = data.get("logs", [])
    usage = data.get("usage", {})
    payload = {
        "runtime_status": status_val,
        "result": combined,
        "member_results": member_results,
        "plan_summary": f"Team execution ({task.team.execution_type.value})",
        "logs": logs,
        "tool_results": [],
        "usage": usage,
        "started_at": data.get("started_at"),
        "completed_at": data.get("completed_at"),
        "workflow_id": str(task.workflow_id) if task.workflow_id else None,
        "attempt_count": task.attempt_count,
    }
    if status_val == "completed":
        return TaskExecutionResult(success=True, payload=payload, error_message=None)
    return TaskExecutionResult(
        success=False,
        payload=payload,
        error_message=combined.get("content") or combined.get("error") or f"Runtime status: {status_val}",
    )


def _call_agent_runtime(
    task: Task,
    past_reflections: list[dict[str, object]] | None = None,
    allowed_tool_slugs: list[str] | None = None,
) -> TaskExecutionResult:
    """Invoke agent-runtime to execute the task and return the result."""
    if task.agent is None:
        return TaskExecutionResult(
            success=False,
            payload={},
            error_message="Agent not loaded for task.",
        )
    agent = task.agent
    base_url = (settings.agent_runtime_url or "").rstrip("/")
    if not base_url:
        return TaskExecutionResult(
            success=False,
            payload={},
            error_message="AGENT_RUNTIME_URL is not configured.",
        )

    tenant_id = str(task.project.tenant_id) if task.project else None
    reflections_list: list[dict[str, object]] = []
    if past_reflections:
        for r in past_reflections:
            if hasattr(r, "success") and hasattr(r, "issues") and hasattr(r, "improvement"):
                reflections_list.append({
                    "success": getattr(r, "success"),
                    "issues": list(getattr(r, "issues", [])) or [],
                    "improvement": getattr(r, "improvement", "") or "",
                })
            elif isinstance(r, dict):
                reflections_list.append(r)
    payload_body = {
        "agent_id": str(agent.id),
        "task_id": str(task.id),
        "model": agent.model,
        "system_prompt": agent.system_prompt or "",
        "task": {
            "title": task.title,
            "description": task.description,
            "input_payload": task.input_payload or {},
        },
        "tool_calls": [],
        "metadata": {
            "tenant_id": tenant_id,
            "project_id": str(task.project_id),
            "workflow_id": str(task.workflow_id) if task.workflow_id else None,
            "past_reflections": reflections_list,
            "allowed_tool_slugs": allowed_tool_slugs,
        },
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{base_url}/api/v1/runs",
                json=payload_body,
                headers={"Content-Type": "application/json"},
            )
    except httpx.ConnectError as e:
        return TaskExecutionResult(
            success=False,
            payload={},
            error_message=f"Agent runtime connection failed: {e!s}",
        )
    except httpx.TimeoutException as e:
        return TaskExecutionResult(
            success=False,
            payload={},
            error_message=f"Agent runtime timeout: {e!s}",
        )
    except Exception as e:
        return TaskExecutionResult(
            success=False,
            payload={},
            error_message=f"Agent runtime error: {e!s}",
        )

    if resp.status_code >= 400:
        err_text = resp.text[:500] if resp.text else ""
        return TaskExecutionResult(
            success=False,
            payload={},
            error_message=f"Agent runtime returned {resp.status_code}: {err_text}",
        )

    data = resp.json()
    status = data.get("status", "unknown")
    result = data.get("result", {})
    logs = data.get("logs", [])
    plan = data.get("plan", {})
    tool_results = data.get("tool_results", [])
    usage = data.get("usage", {})
    completed_at = data.get("completed_at")
    started_at = data.get("started_at")

    reflection_data = data.get("reflection")
    payload = {
        "runtime_status": status,
        "result": result,
        "plan_summary": plan.get("summary", ""),
        "logs": logs,
        "tool_results": tool_results,
        "usage": usage,
        "reflection": reflection_data,
        "started_at": started_at,
        "completed_at": completed_at,
        "workflow_id": str(task.workflow_id) if task.workflow_id else None,
        "attempt_count": task.attempt_count,
    }

    if status == "completed":
        return TaskExecutionResult(success=True, payload=payload, error_message=None)
    return TaskExecutionResult(
        success=False,
        payload=payload,
        error_message=result.get("content") or result.get("raw", {}).get("error") or f"Runtime status: {status}",
    )


def execute_task(
    task: Task,
    past_reflections: list[dict[str, object]] | None = None,
    allowed_tool_slugs: list[str] | None = None,
) -> TaskExecutionResult:
    if task.status == TaskStatus.cancelled:
        return TaskExecutionResult(success=False, payload={}, error_message="Task cancelled before execution.")
    if task.team_id is not None:
        if task.team is None or not task.team.members:
            return TaskExecutionResult(success=False, payload={}, error_message="Task has team_id but team/members not loaded.")
        return _call_team_runtime(task)
    if task.agent_id is None:
        return TaskExecutionResult(success=False, payload={}, error_message="Task has no assigned agent.")

    simulated_failures = int(task.input_payload.get("simulate_failure_attempts", 0))
    if task.attempt_count <= simulated_failures:
        return TaskExecutionResult(
            success=False,
            payload={},
            error_message=f"Simulated worker failure on attempt {task.attempt_count}.",
        )

    return _call_agent_runtime(task, past_reflections=past_reflections, allowed_tool_slugs=allowed_tool_slugs)


def run_worker(poll_sleep_seconds: float = 0.25) -> None:
    if session_factory is None:
        raise RuntimeError("Task worker cannot start without a configured database session factory.")
    configure_logging(settings.service_name)

    while True:
        task_id = dequeue_task()
        if task_id is None:
            time.sleep(poll_sleep_seconds)
            continue

        with session_factory() as session:
            repo = TaskRepository(session)
            service = TaskService(repo)
            task = service.mark_task_running(task_id)
            if task.team_id is not None:
                task = repo.get_with_team(task_id) or task
            if task.status == TaskStatus.cancelled:
                continue

            started_at = datetime.now(timezone.utc)
            log_event(
                settings.service_name,
                EVENT_TASK_START,
                message="Task execution started",
                task_id=str(task.id),
                agent_id=str(task.agent_id) if task.agent_id else None,
                team_id=str(task.team_id) if task.team_id else None,
                project_id=str(task.project_id),
                workflow_id=str(task.workflow_id) if task.workflow_id else None,
            )

            past_reflections = (
                repo.get_recent_reflections_for_agent(task.agent_id, limit=5)
                if task.agent_id
                else []
            )
            allowed_tool_slugs = (
                get_allowed_tool_slugs(session, task.agent_id)
                if task.agent_id
                else None
            )
            result = execute_task(
                task,
                past_reflections=past_reflections,
                allowed_tool_slugs=allowed_tool_slugs,
            )
            completed_at = datetime.now(timezone.utc)
            duration_ms = (completed_at - started_at).total_seconds() * 1000

            if result.success:
                log_event(
                    settings.service_name,
                    EVENT_TASK_FINISH,
                    message="Task execution completed",
                    task_id=str(task.id),
                    status="completed",
                    duration_ms=round(duration_ms, 2),
                    agent_id=str(task.agent_id) if task.agent_id else None,
                    team_id=str(task.team_id) if task.team_id else None,
                )
                service.mark_task_completed(task.id, result.payload)
            else:
                log_event(
                    settings.service_name,
                    EVENT_TASK_FINISH,
                    level="error",
                    message="Task execution failed",
                    task_id=str(task.id),
                    status="failed",
                    duration_ms=round(duration_ms, 2),
                    error=result.error_message,
                    agent_id=str(task.agent_id) if task.agent_id else None,
                    team_id=str(task.team_id) if task.team_id else None,
                )
                log_event(
                    settings.service_name,
                    EVENT_ERROR,
                    level="error",
                    message=result.error_message or "Unknown execution error",
                    task_id=str(task.id),
                    error=result.error_message,
                )
                service.mark_task_failed(
                    task.id,
                    result.error_message or "Unknown execution error.",
                    output_payload=result.payload if result.payload else None,
                )


if __name__ == "__main__":
    run_worker()
