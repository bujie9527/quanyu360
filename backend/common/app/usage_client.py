"""Fire-and-forget usage tracking client. POSTs to admin-service usage ingest API."""
from __future__ import annotations

import structlog

import httpx


def _ingest(base_url: str, payload: dict) -> None:
    """POST to /admin/usage/ingest. Fail silently."""
    try:
        url = f"{base_url.rstrip('/')}/admin/usage/ingest"
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code >= 400:
                structlog.get_logger("usage_client").warning(
                    "usage_ingest_failed",
                    status=resp.status_code,
                    body=resp.text[:200],
                )
    except Exception as exc:
        structlog.get_logger("usage_client").warning("usage_ingest_error", error=str(exc))


def track_llm_tokens(
    base_url: str | None,
    *,
    tenant_id: str,
    project_id: str | None = None,
    prompt_tokens: int,
    completion_tokens: int,
    model: str | None = None,
    provider: str | None = None,
    agent_id: str | None = None,
    task_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    """Track LLM token usage."""
    if not base_url or not tenant_id:
        return
    _ingest(
        base_url,
        {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "usage_type": "llm_tokens",
            "prompt_tokens": max(0, prompt_tokens),
            "completion_tokens": max(0, completion_tokens),
            "quantity": max(0, prompt_tokens) + max(0, completion_tokens),
            "metadata": {
                **(metadata or {}),
                "model": model,
                "provider": provider,
                "agent_id": agent_id,
                "task_id": task_id,
            },
        },
    )


def track_workflow_run(
    base_url: str | None,
    *,
    tenant_id: str,
    project_id: str | None = None,
    workflow_id: str | None = None,
    execution_id: str | None = None,
    status: str | None = None,
    metadata: dict | None = None,
) -> None:
    """Track workflow execution."""
    if not base_url or not tenant_id:
        return
    _ingest(
        base_url,
        {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "usage_type": "workflow_run",
            "quantity": 1,
            "metadata": {
                **(metadata or {}),
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "status": status,
            },
        },
    )


def track_tool_execution(
    base_url: str | None,
    *,
    tenant_id: str,
    project_id: str | None = None,
    tool_name: str,
    action: str,
    agent_id: str | None = None,
    task_id: str | None = None,
    workflow_id: str | None = None,
    execution_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    """Track tool execution."""
    if not base_url or not tenant_id:
        return
    _ingest(
        base_url,
        {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "usage_type": "tool_execution",
            "quantity": 1,
            "metadata": {
                **(metadata or {}),
                "tool_name": tool_name,
                "action": action,
                "agent_id": agent_id,
                "task_id": task_id,
                "workflow_id": workflow_id,
                "execution_id": execution_id,
            },
        },
    )
