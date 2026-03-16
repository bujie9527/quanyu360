"""AgentInstance data access."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from common.app.models import AgentInstance
from common.app.models import AgentTemplate
from common.app.models import Project


class AgentInstanceRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        project_id: UUID | None = None,
        tenant_id: UUID | None = None,
        template_id: UUID | None = None,
        enabled: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AgentInstance], int]:
        stmt = select(AgentInstance).options(
            joinedload(AgentInstance.template),
            joinedload(AgentInstance.project),
            joinedload(AgentInstance.knowledge_base),
        )
        count_stmt = select(func.count(AgentInstance.id))
        if project_id is not None:
            stmt = stmt.where(AgentInstance.project_id == project_id)
            count_stmt = count_stmt.where(AgentInstance.project_id == project_id)
        if tenant_id is not None:
            stmt = stmt.where(AgentInstance.tenant_id == tenant_id)
            count_stmt = count_stmt.where(AgentInstance.tenant_id == tenant_id)
        if template_id is not None:
            stmt = stmt.where(AgentInstance.template_id == template_id)
            count_stmt = count_stmt.where(AgentInstance.template_id == template_id)
        if enabled is not None:
            stmt = stmt.where(AgentInstance.enabled.is_(enabled))
            count_stmt = count_stmt.where(AgentInstance.enabled.is_(enabled))
        items = list(
            self.db.scalars(
                stmt.order_by(AgentInstance.created_at.desc()).offset(offset).limit(limit)
            ).unique().all()
        )
        total = self.db.scalar(count_stmt) or 0
        return items, total

    def get(self, instance_id: UUID) -> AgentInstance | None:
        return self.db.scalar(
            select(AgentInstance)
            .options(
                joinedload(AgentInstance.template),
                joinedload(AgentInstance.project),
                joinedload(AgentInstance.knowledge_base),
            )
            .where(AgentInstance.id == instance_id)
        )

    def add(self, instance: AgentInstance) -> None:
        self.db.add(instance)
        self.db.flush()

    def delete(self, instance: AgentInstance) -> None:
        self.db.delete(instance)

    def get_template(self, template_id: UUID) -> AgentTemplate | None:
        return self.db.get(AgentTemplate, template_id)

    def get_project(self, project_id: UUID) -> Project | None:
        return self.db.get(Project, project_id)
