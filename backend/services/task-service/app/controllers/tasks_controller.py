"""Task HTTP endpoints."""
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status

from app.dependencies import get_task_service
from app.metrics import render_prometheus_metrics
from app.schemas import TaskAnalyticsSummaryResponse
from app.schemas import TaskCancelResponse
from app.schemas import TaskCreateRequest
from app.schemas import TaskDetailResponse
from app.schemas import TaskListResponse
from app.schemas import TaskRunResponse
from app.schemas import TaskSummaryResponse
from app.services import TaskService
from common.app.models import Task
from common.app.models import TaskPriority
from common.app.models import TaskStatus
from common.app.observability.prometheus import build_metrics_response

router = APIRouter()


def _build_task_summary(task: Task) -> TaskSummaryResponse:
    return TaskSummaryResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status.value,
        priority=task.priority.value,
        project_id=task.project_id,
        agent_id=task.agent_id,
        team_id=task.team_id,
        workflow_id=task.workflow_id,
        attempt_count=task.attempt_count,
        max_attempts=task.max_attempts,
        due_at=task.due_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _build_task_detail(task: Task) -> TaskDetailResponse:
    return TaskDetailResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status.value,
        priority=task.priority.value,
        project_id=task.project_id,
        agent_id=task.agent_id,
        team_id=task.team_id,
        workflow_id=task.workflow_id,
        created_by_user_id=task.created_by_user_id,
        attempt_count=task.attempt_count,
        max_attempts=task.max_attempts,
        last_error=task.last_error,
        due_at=task.due_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        input_payload=task.input_payload,
        output_payload=task.output_payload,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("/metrics", tags=["observability"])
def metrics(task_service: TaskService = Depends(get_task_service)):
    summary = task_service.get_task_analytics_summary()
    return build_metrics_response(render_prometheus_metrics(summary))


@router.post("/tasks", response_model=TaskDetailResponse, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(
    payload: TaskCreateRequest,
    task_service: TaskService = Depends(get_task_service),
) -> TaskDetailResponse:
    task = task_service.create_task(payload)
    return _build_task_detail(task)


@router.get("/tasks", response_model=TaskListResponse, tags=["tasks"])
def list_tasks(
    project_id: UUID | None = Query(default=None),
    agent_id: UUID | None = Query(default=None),
    workflow_id: UUID | None = Query(default=None),
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    priority: TaskPriority | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    task_service: TaskService = Depends(get_task_service),
) -> TaskListResponse:
    items, total = task_service.list_tasks(
        project_id=project_id,
        agent_id=agent_id,
        workflow_id=workflow_id,
        status_filter=status_filter,
        priority=priority,
        search=search,
        limit=limit,
        offset=offset,
    )
    return TaskListResponse(
        items=[_build_task_summary(t) for t in items],
        total=total,
    )


@router.get("/tasks/analytics", response_model=TaskAnalyticsSummaryResponse, tags=["analytics"])
def get_task_analytics(task_service: TaskService = Depends(get_task_service)) -> TaskAnalyticsSummaryResponse:
    return task_service.get_task_analytics_summary()


@router.get("/tasks/{task_id}", response_model=TaskDetailResponse, tags=["tasks"])
def get_task(
    task_id: UUID,
    task_service: TaskService = Depends(get_task_service),
) -> TaskDetailResponse:
    task = task_service.get_task(task_id)
    return _build_task_detail(task)


@router.post("/tasks/{task_id}/run", response_model=TaskRunResponse, tags=["tasks"])
def run_task(
    task_id: UUID,
    task_service: TaskService = Depends(get_task_service),
) -> TaskRunResponse:
    task = task_service.run_task(task_id)
    return TaskRunResponse(
        task_id=task.id,
        status=task.status.value,
        queued=True,
        attempt_count=task.attempt_count,
        max_attempts=task.max_attempts,
    )


@router.post("/tasks/{task_id}/cancel", response_model=TaskCancelResponse, tags=["tasks"])
def cancel_task(
    task_id: UUID,
    task_service: TaskService = Depends(get_task_service),
) -> TaskCancelResponse:
    task = task_service.cancel_task(task_id)
    return TaskCancelResponse(
        task_id=task.id,
        status=task.status.value,
        cancelled=True,
    )
