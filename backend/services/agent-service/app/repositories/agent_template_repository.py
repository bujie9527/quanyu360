"""AgentTemplate data access."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from common.app.models import AgentTemplate


class AgentTemplateRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        enabled: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AgentTemplate], int]:
        stmt = select(AgentTemplate)
        count_stmt = select(func.count(AgentTemplate.id))
        if enabled is not None:
            stmt = stmt.where(AgentTemplate.enabled.is_(enabled))
            count_stmt = count_stmt.where(AgentTemplate.enabled.is_(enabled))
        items = list(
            self.db.scalars(stmt.order_by(AgentTemplate.created_at.desc()).offset(offset).limit(limit)).unique().all()
        )
        total = self.db.scalar(count_stmt) or 0
        return items, total

    def get(self, template_id: UUID) -> AgentTemplate | None:
        return self.db.get(AgentTemplate, template_id)

    def add(self, template: AgentTemplate) -> None:
        self.db.add(template)
        self.db.flush()

    def delete(self, template: AgentTemplate) -> None:
        self.db.delete(template)
