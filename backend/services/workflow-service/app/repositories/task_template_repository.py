"""TaskTemplate data access."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from common.app.models import TaskTemplate


class TaskTemplateRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        project_id: UUID | None = None,
        workflow_id: UUID | None = None,
        enabled: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TaskTemplate], int]:
        stmt = select(TaskTemplate)
        count_stmt = select(func.count(TaskTemplate.id))
        if project_id is not None:
            stmt = stmt.where(TaskTemplate.project_id == project_id)
            count_stmt = count_stmt.where(TaskTemplate.project_id == project_id)
        if workflow_id is not None:
            stmt = stmt.where(TaskTemplate.workflow_id == workflow_id)
            count_stmt = count_stmt.where(TaskTemplate.workflow_id == workflow_id)
        if enabled is not None:
            stmt = stmt.where(TaskTemplate.enabled.is_(enabled))
            count_stmt = count_stmt.where(TaskTemplate.enabled.is_(enabled))

        items = list(
            self.db.scalars(
                stmt.order_by(TaskTemplate.created_at.desc()).offset(offset).limit(limit)
            ).all()
        )
        total = self.db.scalar(count_stmt) or 0
        return items, total

    def get(self, template_id: UUID) -> TaskTemplate | None:
        return self.db.get(TaskTemplate, template_id)

    def add(self, template: TaskTemplate) -> None:
        self.db.add(template)
        self.db.flush()

    def delete(self, template: TaskTemplate) -> None:
        self.db.delete(template)
