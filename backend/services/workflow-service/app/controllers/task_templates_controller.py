"""TaskTemplate HTTP endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.repositories import TaskTemplateRepository
from app.repositories import WorkflowRepository
from app.schemas.task_template_schemas import TaskTemplateCreateRequest
from app.schemas.task_template_schemas import TaskTemplateListResponse
from app.schemas.task_template_schemas import TaskTemplateResponse
from app.services.task_template_service import TaskTemplateService
from common.app.models import TaskTemplate

router = APIRouter(prefix="/task_templates", tags=["task-templates"])


def _get_service(db: Session = Depends(get_db_session)) -> TaskTemplateService:
    return TaskTemplateService(
        task_template_repo=TaskTemplateRepository(db),
        workflow_repo=WorkflowRepository(db),
    )


def _to_response(t: TaskTemplate) -> TaskTemplateResponse:
    return TaskTemplateResponse(
        id=t.id,
        project_id=t.project_id,
        name=t.name,
        description=t.description,
        workflow_id=t.workflow_id,
        parameters_schema=t.parameters_schema or {},
        enabled=t.enabled,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.post("", response_model=TaskTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_task_template(
    payload: TaskTemplateCreateRequest,
    service: TaskTemplateService = Depends(_get_service),
) -> TaskTemplateResponse:
    """创建任务模板。"""
    template = service.create_template(payload)
    return _to_response(template)


@router.get("", response_model=TaskTemplateListResponse)
def list_task_templates(
    project_id: UUID | None = Query(default=None),
    workflow_id: UUID | None = Query(default=None),
    enabled: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: TaskTemplateService = Depends(_get_service),
) -> TaskTemplateListResponse:
    """获取任务模板列表。"""
    items, total = service.list_templates(
        project_id=project_id,
        workflow_id=workflow_id,
        enabled=enabled,
        limit=limit,
        offset=offset,
    )
    return TaskTemplateListResponse(
        items=[_to_response(t) for t in items],
        total=total,
    )


@router.get("/{template_id}", response_model=TaskTemplateResponse)
def get_task_template(
    template_id: UUID,
    service: TaskTemplateService = Depends(_get_service),
) -> TaskTemplateResponse:
    """获取任务模板详情。"""
    template = service.get_template(template_id)
    return _to_response(template)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_template(
    template_id: UUID,
    service: TaskTemplateService = Depends(_get_service),
) -> None:
    """删除任务模板。"""
    service.delete_template(template_id)
