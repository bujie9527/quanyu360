"""Task request/response schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

from common.app.models import TaskPriority
from common.app.models import TaskStatus


class TaskCreateRequest(BaseModel):
    project_id: UUID
    agent_id: UUID | None = None
    team_id: UUID | None = None
    workflow_id: UUID | None = None
    created_by_user_id: UUID | None = None
    title: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    priority: TaskPriority = TaskPriority.normal
    max_attempts: int = Field(default=3, ge=1, le=20)
    due_at: datetime | None = None
    input_payload: dict[str, object] = Field(default_factory=dict)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        return value.strip()


class TaskRunResponse(BaseModel):
    task_id: UUID
    status: str
    queued: bool
    attempt_count: int
    max_attempts: int


class TaskCancelResponse(BaseModel):
    task_id: UUID
    status: str
    cancelled: bool


class TaskSummaryResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: str
    priority: str
    project_id: UUID
    agent_id: UUID | None
    team_id: UUID | None = None
    workflow_id: UUID | None
    attempt_count: int
    max_attempts: int
    due_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TaskDetailResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: str
    priority: str
    project_id: UUID
    agent_id: UUID | None
    team_id: UUID | None = None
    workflow_id: UUID | None
    created_by_user_id: UUID | None
    attempt_count: int
    max_attempts: int
    last_error: str | None
    due_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    input_payload: dict[str, object]
    output_payload: dict[str, object]
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    items: list[TaskSummaryResponse]
    total: int


class AnalyticsPointResponse(BaseModel):
    label: str
    value: float


class TaskAnalyticsSummaryResponse(BaseModel):
    tasks_executed: int
    completed_tasks: int
    failed_tasks: int
    pending_tasks: int
    running_tasks: int
    agent_success_rate: float
    average_execution_time_seconds: float
    p95_execution_time_seconds: float
    status_breakdown: list[AnalyticsPointResponse]
    recent_task_volume: list[AnalyticsPointResponse]
    execution_time_breakdown: list[AnalyticsPointResponse]
