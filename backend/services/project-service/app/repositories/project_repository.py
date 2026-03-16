"""Project data access layer."""
from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import Select
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload

from common.app.models import Agent
from common.app.models import Project
from common.app.models import ProjectStatus
from common.app.models import ProjectTeamMember
from common.app.models import Tenant
from common.app.models import User
from common.app.models import UserStatus
from common.app.models import Workflow


class ProjectRepository:
    """Handles database access for projects."""

    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        tenant_id: UUID | None = None,
        owner_id: UUID | None = None,
        status_filter: ProjectStatus | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Project], int]:
        statement = self._base_statement()
        count_statement = select(func.count(Project.id))
        statement, count_statement = self._apply_filters(
            statement, count_statement, tenant_id, owner_id, status_filter, search
        )
        items = self.db.scalars(
            statement.order_by(Project.created_at.desc()).offset(offset).limit(limit)
        ).unique().all()
        total = self.db.scalar(count_statement) or 0
        return items, total

    def get(self, project_id: UUID) -> Project | None:
        return self.db.scalar(
            self._base_statement().where(Project.id == project_id)
        )

    def add(self, project: Project) -> None:
        self.db.add(project)
        self.db.flush()

    def delete(self, project: Project) -> None:
        self.db.delete(project)

    def exists_by_key(self, tenant_id: UUID, key: str) -> bool:
        return self.db.scalar(
            select(Project.id).where(Project.tenant_id == tenant_id, Project.key == key)
        ) is not None

    def generate_project_key(self, tenant_id: UUID, name: str) -> str:
        tokens = re.findall(r"[A-Za-z0-9]+", name.upper())
        base_key = "".join(token[0] for token in tokens[:8]) if len(tokens) > 1 else "".join(tokens)[:8]
        base_key = re.sub(r"[^A-Z0-9]", "", base_key) or "PRJ"
        candidate = base_key[:32]
        suffix = 1
        while self.exists_by_key(tenant_id, candidate):
            suffix += 1
            candidate = f"{base_key[:28]}{suffix}"
        return candidate

    def get_tenant(self, tenant_id: UUID) -> Tenant | None:
        return self.db.get(Tenant, tenant_id)

    def get_user_in_tenant(self, user_id: UUID, tenant_id: UUID) -> User | None:
        return self.db.scalar(
            select(User).where(
                User.id == user_id,
                User.tenant_id == tenant_id,
                User.status == UserStatus.active,
            )
        )

    def get_agents_by_ids(self, agent_ids: list[UUID]) -> list[Agent]:
        if not agent_ids:
            return []
        return list(
            self.db.scalars(
                select(Agent)
                .options(joinedload(Agent.project), selectinload(Agent.tasks))
                .where(Agent.id.in_(agent_ids))
            ).unique().all()
        )

    def get_workflows_by_ids(self, workflow_ids: list[UUID]) -> list[Workflow]:
        if not workflow_ids:
            return []
        return list(
            self.db.scalars(
                select(Workflow)
                .options(joinedload(Workflow.project), selectinload(Workflow.tasks))
                .where(Workflow.id.in_(workflow_ids))
            ).unique().all()
        )

    def _base_statement(self) -> Select[tuple[Project]]:
        return select(Project).options(
            selectinload(Project.team_memberships).selectinload(ProjectTeamMember.user),
            selectinload(Project.agents),
            selectinload(Project.tasks),
            selectinload(Project.workflows),
        )

    def _apply_filters(
        self,
        statement: Select,
        count_statement: Select,
        tenant_id: UUID | None,
        owner_id: UUID | None,
        status_filter: ProjectStatus | None,
        search: str | None,
    ) -> tuple[Select, Select]:
        if tenant_id is not None:
            statement = statement.where(Project.tenant_id == tenant_id)
            count_statement = count_statement.where(Project.tenant_id == tenant_id)
        if owner_id is not None:
            statement = statement.where(Project.owner_user_id == owner_id)
            count_statement = count_statement.where(Project.owner_user_id == owner_id)
        if status_filter is not None:
            statement = statement.where(Project.status == status_filter)
            count_statement = count_statement.where(Project.status == status_filter)
        if search:
            search_term = f"%{search.strip()}%"
            predicate = or_(Project.name.ilike(search_term), Project.description.ilike(search_term))
            statement = statement.where(predicate)
            count_statement = count_statement.where(predicate)
        return statement, count_statement
