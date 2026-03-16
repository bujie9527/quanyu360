"""Dashboard response schemas."""
from __future__ import annotations

from pydantic import BaseModel


class SystemHealthResponse(BaseModel):
    database: str
    project_service: str
    agent_service: str
    task_service: str
    workflow_service: str


class DashboardResponse(BaseModel):
    total_users: int
    total_tenants: int
    total_projects: int
    total_agents: int
    total_tasks: int
    total_workflows: int
    system_health: dict[str, str]
