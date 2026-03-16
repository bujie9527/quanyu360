"""Cron-based scheduler for workflow triggers. Runs scheduled workflows at cron times."""
from __future__ import annotations

import logging
from datetime import datetime
from datetime import timezone
from typing import Any

import httpx
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from croniter import croniter

logger = logging.getLogger(__name__)


def _get_workflow_service_url() -> str:
    from app.core.config import get_settings
    return get_settings().workflow_service_url or "http://workflow-service:8005"


def _get_workflow_engine_url() -> str:
    from app.core.config import get_settings
    return get_settings().workflow_engine_url or "http://workflow-engine:8100"


def _fetch_scheduled_workflows() -> list[dict[str, Any]]:
    """Fetch active workflows with scheduled trigger from workflow-service."""
    base = _get_workflow_service_url().rstrip("/")
    url = f"{base}/workflows/scheduled"
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url)
            if resp.status_code != 200:
                logger.warning("Scheduler: failed to fetch workflows: %s", resp.status_code)
                return []
            data = resp.json()
            return data.get("items", [])
    except Exception as exc:
        logger.warning("Scheduler: fetch error: %s", exc)
        return []


def _get_cron_for_workflow(wf: dict[str, Any]) -> str | None:
    """Extract cron expression from workflow config."""
    definition = wf.get("definition") or {}
    config = definition.get("configuration") or {}
    trigger_cfg = config.get("trigger_config") or config
    schedule = trigger_cfg.get("schedule")
    if isinstance(schedule, dict):
        return schedule.get("cron")
    return None


def _execute_workflow(workflow_id: str, tenant_id: str | None = None) -> bool:
    """Trigger workflow execution via workflow-service."""
    base = _get_workflow_service_url().rstrip("/")
    url = f"{base}/workflows/{workflow_id}/execute"
    payload = {"input_payload": {"trigger": "schedule", "triggered_at": datetime.now(timezone.utc).isoformat()}}
    if tenant_id:
        payload["input_payload"]["tenant_id"] = tenant_id
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code in (200, 201, 202):
                logger.info("Scheduler: triggered workflow %s", workflow_id)
                return True
            logger.warning("Scheduler: trigger failed %s: %s", workflow_id, resp.status_code)
            return False
    except Exception as exc:
        logger.warning("Scheduler: execute error for %s: %s", workflow_id, exc)
        return False


def _tick_schedules() -> None:
    """Check Schedule table and trigger due schedule -> task_template -> workflow."""
    base = _get_workflow_service_url().rstrip("/")
    url = f"{base}/schedules/tick"
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("triggered", 0) > 0:
                    logger.info("Scheduler: triggered %d schedule(s)", data["triggered"])
            else:
                logger.warning("Scheduler: schedules tick failed: %s", resp.status_code)
    except Exception as exc:
        logger.warning("Scheduler: schedules tick error: %s", exc)


def _tick() -> None:
    """Check scheduled workflows and Schedule table, trigger those due now."""
    now = datetime.now(timezone.utc)

    # 1. Schedule 表: schedule -> task_template -> workflow
    _tick_schedules()

    # 2. Workflow 自带 scheduled trigger
    workflows = _fetch_scheduled_workflows()
    for wf in workflows:
        wf_id = str(wf.get("id", ""))
        cron_expr = _get_cron_for_workflow(wf)
        if not cron_expr or not croniter.is_valid(cron_expr):
            continue
        if croniter.match(cron_expr, now):
            tenant_id = None
            project = wf.get("project")
            if isinstance(project, dict) and project.get("tenant_id"):
                tenant_id = str(project["tenant_id"])
            _execute_workflow(wf_id, tenant_id)


def start_scheduler() -> BackgroundScheduler:
    """Start APScheduler; ticks every minute for workflows + Schedule table."""
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(_tick, CronTrigger(minute="*", second="0"), id="schedule_tick")
    scheduler.start()
    logger.info("Workflow trigger scheduler started (cron check every minute)")
    return scheduler


def stop_scheduler(scheduler: BackgroundScheduler | None) -> None:
    """Shutdown scheduler."""
    if scheduler:
        try:
            scheduler.shutdown(wait=False)
        except Exception:
            pass
