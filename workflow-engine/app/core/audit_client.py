"""Fire-and-forget audit log client. POSTs to admin-service audit ingest API."""
from __future__ import annotations

import structlog

import httpx


def _ingest(base_url: str, payload: dict) -> None:
    """POST to /api/admin/audit/ingest. Fail silently."""
    try:
        url = f"{base_url.rstrip('/')}/api/admin/audit/ingest"
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


def log_tool_call(
    base_url: str | None,
    *,
    tenant_id: str,
    project_id: str | None,
    agent_id: str | None,
    workflow_id: str | None,
    execution_id: str | None,
    tool_name: str,
    action: str,
    success: bool,
    node_key: str | None = None,
) -> None:
    """Log workflow tool node execution."""
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
            "correlation_id": execution_id or "",
            "payload": {
                "agent_id": agent_id,
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "node_key": node_key,
                "tool_name": tool_name,
                "action": action,
                "success": success,
                "source": "workflow",
            },
        },
    )


def log_workflow_execution(
    base_url: str | None,
    *,
    tenant_id: str,
    project_id: str | None,
    workflow_id: str,
    execution_id: str,
    status: str,
    payload: dict | None = None,
) -> None:
    """Log workflow execution start or completion."""
    if not base_url:
        return
    _ingest(
        base_url,
        {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "action": "execute",
            "entity_type": "workflow_execution",
            "entity_id": None,
            "correlation_id": execution_id,
            "payload": {
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "status": status,
                **(payload or {}),
            },
        },
    )
