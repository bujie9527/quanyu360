"""TaskTemplate business logic."""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from fastapi import status

from app.repositories import TaskTemplateRepository
from app.repositories import WorkflowRepository
from app.schemas.task_template_schemas import TaskTemplateCreateRequest
from app.schemas.task_template_schemas import TaskTemplateUpdateRequest
from common.app.models import TaskTemplate


class TaskTemplateService:
    def __init__(
        self,
        task_template_repo: TaskTemplateRepository,
        workflow_repo: WorkflowRepository | None = None,
    ):
        self.repo = task_template_repo
        self.workflow_repo = workflow_repo

    def list_templates(
        self,
        project_id: UUID | None = None,
        workflow_id: UUID | None = None,
        enabled: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TaskTemplate], int]:
        return self.repo.list(
            project_id=project_id,
            workflow_id=workflow_id,
            enabled=enabled,
            limit=limit,
            offset=offset,
        )

    def get_template(self, template_id: UUID) -> TaskTemplate:
        t = self.repo.get(template_id)
        if t is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务模板不存在")
        return t

    def create_template(self, payload: TaskTemplateCreateRequest) -> TaskTemplate:
        if payload.workflow_id and self.workflow_repo:
            wf = self.workflow_repo.get(payload.workflow_id)
            if wf is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow 不存在")
            if wf.project_id != payload.project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Workflow 必须属于同一项目",
                )

        template = TaskTemplate(
            project_id=payload.project_id,
            name=payload.name,
            description=payload.description,
            workflow_id=payload.workflow_id,
            parameters_schema=payload.parameters_schema,
            enabled=payload.enabled,
        )
        self.repo.add(template)
        self.repo.db.commit()
        self.repo.db.refresh(template)
        return template

    def delete_template(self, template_id: UUID) -> None:
        t = self.get_template(template_id)
        self.repo.delete(t)
        self.repo.db.commit()
