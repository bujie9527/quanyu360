"""Persist StepRun to workflow-service. Called after each workflow step."""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _get_workflow_service_url() -> str:
    from app.core.config import get_settings
    return (get_settings().workflow_service_url or "http://workflow-service:8005").rstrip("/")


def log_step_run(
    task_run_id: str,
    step_name: str,
    status: str,
    duration: float,
    output: dict[str, Any],
) -> None:
    """POST step to workflow-service task_runs/{id}/steps. Fail silently."""
    base = _get_workflow_service_url()
    url = f"{base}/task_runs/{task_run_id}/steps"
    payload = {
        "step_name": step_name,
        "status": status,
        "duration": duration,
        "output_json": output or {},
    }
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code >= 400:
                logger.warning("execution_log: step persist failed %s: %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.warning("execution_log: step persist error: %s", exc)


def update_task_run_status(task_run_id: str, status: str, end_time: str | None = None) -> None:
    """PATCH task_runs/{id} to update status. Fail silently."""
    base = _get_workflow_service_url()
    url = f"{base}/task_runs/{task_run_id}"
    payload = {"status": status}
    if end_time:
        payload["end_time"] = end_time
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.patch(url, json=payload)
            if resp.status_code >= 400:
                logger.warning("execution_log: task_run update failed %s: %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.warning("execution_log: task_run update error: %s", exc)
