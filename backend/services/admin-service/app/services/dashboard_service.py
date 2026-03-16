"""Dashboard aggregation logic."""
from __future__ import annotations

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

import httpx

from app.config import settings
from common.app.models import Tenant
from common.app.models import User


def get_dashboard(
    auth_session: Session,
    project_service_url: str | None = None,
    agent_service_url: str | None = None,
    task_service_url: str | None = None,
    workflow_service_url: str | None = None,
) -> dict:
    """Aggregate dashboard stats from auth_db and downstream services."""
    project_url = project_service_url or settings.project_service_url
    agent_url = agent_service_url or settings.agent_service_url
    task_url = task_service_url or settings.task_service_url
    workflow_url = workflow_service_url or settings.workflow_service_url

    total_users = auth_session.scalar(select(func.count(User.id))) or 0
    total_tenants = auth_session.scalar(select(func.count(Tenant.id))) or 0

    total_projects = _fetch_total_from_service(project_url, "/projects")
    total_agents = _fetch_total_from_service(agent_url, "/agents")
    total_tasks = _fetch_total_from_service(task_url, "/tasks")
    total_workflows = _fetch_total_from_service(workflow_url, "/workflows")

    system_health = _check_system_health(
        auth_session=auth_session,
        project_url=project_url,
        agent_url=agent_url,
        task_url=task_url,
        workflow_url=workflow_url,
    )

    return {
        "total_users": total_users,
        "total_tenants": total_tenants,
        "total_projects": total_projects,
        "total_agents": total_agents,
        "total_tasks": total_tasks,
        "total_workflows": total_workflows,
        "system_health": system_health,
    }


def _fetch_total_from_service(base_url: str, path: str) -> int:
    try:
        url = f"{base_url.rstrip('/')}{path}"
        with httpx.Client(timeout=5.0) as client:
            r = client.get(url, params={"limit": 1, "offset": 0})
            r.raise_for_status()
            data = r.json()
            return data.get("total", 0)
    except Exception:
        return 0


def _check_system_health(
    auth_session: Session,
    project_url: str,
    agent_url: str,
    task_url: str,
    workflow_url: str,
) -> dict:
    health = {
        "database": "unknown",
        "project_service": "unknown",
        "agent_service": "unknown",
        "task_service": "unknown",
        "workflow_service": "unknown",
    }
    try:
        auth_session.execute(select(1))
        health["database"] = "ok"
    except Exception:
        health["database"] = "error"
    health["project_service"] = "ok" if _ping(f"{project_url.rstrip('/')}/health/live") else "error"
    health["agent_service"] = "ok" if _ping(f"{agent_url.rstrip('/')}/health/live") else "error"
    health["task_service"] = "ok" if _ping(f"{task_url.rstrip('/')}/health/live") else "error"
    health["workflow_service"] = "ok" if _ping(f"{workflow_url.rstrip('/')}/health/live") else "error"
    return health


def _ping(url: str) -> bool:
    try:
        with httpx.Client(timeout=3.0) as client:
            r = client.get(url)
            return r.status_code == 200
    except Exception:
        return False
