"""Fire-and-forget AgentRun ingest. POSTs to agent-service /agent/runs."""
from __future__ import annotations

import structlog

import httpx


def ingest_agent_run(
    base_url: str | None,
    *,
    agent_id: str,
    run_type: str,
    input_payload: dict,
    output_payload: dict,
    status: str,
) -> None:
    """写入 AgentRun 日志。失败时静默，不阻塞主流程。"""
    if not base_url:
        return
    try:
        url = f"{base_url.rstrip('/')}/agent/runs"
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(
                url,
                json={
                    "agent_id": agent_id,
                    "type": run_type,
                    "input": input_payload,
                    "output": output_payload,
                    "status": status,
                },
            )
            if resp.status_code >= 400:
                structlog.get_logger("agent_run_client").warning(
                    "agent_run_ingest_failed",
                    status=resp.status_code,
                    body=resp.text[:200],
                )
    except Exception as exc:
        structlog.get_logger("agent_run_client").warning(
            "agent_run_ingest_error", error=str(exc)
        )
