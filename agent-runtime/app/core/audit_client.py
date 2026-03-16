"""Fire-and-forget audit log client. POSTs to admin-service audit ingest API."""
from __future__ import annotations

import structlog

import httpx


def _ingest(base_url: str, payload: dict) -> None:
    """POST to /admin/audit/ingest. Fail silently."""
    try:
        url = f"{base_url.rstrip('/')}/admin/audit/ingest"
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code >= 400:
                structlog.get_logger("audit_client").warning(
                    "audit_ingest_failed",
                    status=resp.status_code,
                    body=resp.text[:200],
                )
    except Exception as exc:
        structlog.get_logger("audit_client").warning("audit_ingest_error", error=str(exc))


def log_agent_run(
    base_url: str | None,
    *,
    tenant_id: str,
    project_id: str | None,
    agent_id: str,
    task_id: str,
    status: str,
    correlation_id: str | None = None,
    payload: dict | None = None,
) -> None:
    """Log agent execution completion."""
    if not base_url:
        return
    _ingest(
        base_url,
        {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "action": "execute",
            "entity_type": "agent_run",
            "entity_id": None,
            "correlation_id": correlation_id or task_id,
            "payload": {
                "agent_id": agent_id,
                "task_id": task_id,
                "status": status,
                **(payload or {}),
            },
        },
    )


def log_tool_call(
    base_url: str | None,
    *,
    tenant_id: str,
    project_id: str | None,
    agent_id: str | None,
    task_id: str | None,
    tool_name: str,
    action: str,
    success: bool,
    correlation_id: str | None = None,
) -> None:
    """Log tool usage."""
    if not base_url:
        return
    _ingest(
        base_url,
        {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "action": "execute",
            "entity_type": "tool_call",
            "entity_id": None,
            "correlation_id": correlation_id or task_id or "",
            "payload": {
                "agent_id": agent_id,
                "task_id": task_id,
                "tool_name": tool_name,
                "action": action,
                "success": success,
            },
        },
    )
