"""Agent data access layer."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload

from common.app.models import Agent
from common.app.models import AgentStatus
from common.app.models import AgentToolLink
from common.app.models import AgentToolPermission
from common.app.models import AgentWorkflowLink
from common.app.models import Project
from common.app.models import Task
from common.app.models import Tool
from common.app.models import User
from common.app.models import UserStatus
from common.app.models import Workflow


class AgentRepository:
    """Handles database access for agents."""

    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        project_id: UUID | None = None,
        status_filter: AgentStatus | None = None,
        role: str | None = None,
        model: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Agent], int]:
        statement = self._base_statement()
        count_statement = select(func.count(Agent.id))
        if project_id is not None:
            statement = statement.where(Agent.project_id == project_id)
            count_statement = count_statement.where(Agent.project_id == project_id)
        if status_filter is not None:
            statement = statement.where(Agent.status == status_filter)
            count_statement = count_statement.where(Agent.status == status_filter)
        if role is not None:
            statement = statement.where(Agent.role == role)
            count_statement = count_statement.where(Agent.role == role)
        if model is not None:
            statement = statement.where(Agent.model == model)
            count_statement = count_statement.where(Agent.model == model)
        if search:
            term = f"%{search.strip()}%"
            pred = or_(
                Agent.name.ilike(term),
                Agent.role.ilike(term),
                Agent.role_title.ilike(term),
                Agent.model.ilike(term),
            )
            statement = statement.where(pred)
            count_statement = count_statement.where(pred)
        items = self.db.scalars(
            statement.order_by(Agent.created_at.desc()).offset(offset).limit(limit)
        ).unique().all()
        total = self.db.scalar(count_statement) or 0
        return items, total

    def get(self, agent_id: UUID) -> Agent | None:
        return self.db.scalar(self._base_statement().where(Agent.id == agent_id))

    def add(self, agent: Agent) -> None:
        self.db.add(agent)
        self.db.flush()

    def delete(self, agent: Agent) -> None:
        self.db.delete(agent)

    def slug_exists(self, project_id: UUID, slug: str, exclude_agent_id: UUID | None = None) -> bool:
        stmt = select(Agent.id).where(Agent.project_id == project_id, Agent.slug == slug)
        if exclude_agent_id is not None:
            stmt = stmt.where(Agent.id != exclude_agent_id)
        return self.db.scalar(stmt.limit(1)) is not None

    def has_tasks(self, agent_id: UUID) -> bool:
        return self.db.scalar(select(Task.id).where(Task.agent_id == agent_id).limit(1)) is not None

    def get_project(self, project_id: UUID) -> Project | None:
        return self.db.get(Project, project_id)

    def get_user_in_tenant(self, user_id: UUID, tenant_id: UUID) -> User | None:
        return self.db.scalar(
            select(User).where(
                User.id == user_id,
                User.tenant_id == tenant_id,
                User.status == UserStatus.active,
            )
        )

    def get_tools_by_ids(self, tool_ids: list[UUID]) -> list[Tool]:
        if not tool_ids:
            return []
        return list(self.db.scalars(select(Tool).where(Tool.id.in_(tool_ids))).all())

    def get_workflows_by_ids(self, workflow_ids: list[UUID]) -> list[Workflow]:
        if not workflow_ids:
            return []
        return list(self.db.scalars(select(Workflow).where(Workflow.id.in_(workflow_ids))).all())

    def _base_statement(self) -> Select[tuple[Agent]]:
        return select(Agent).options(
            joinedload(Agent.project),
            selectinload(Agent.skills),
            selectinload(Agent.tool_links).joinedload(AgentToolLink.tool),
            selectinload(Agent.tool_permissions),
            selectinload(Agent.workflow_links).joinedload(AgentWorkflowLink.workflow),
        )
