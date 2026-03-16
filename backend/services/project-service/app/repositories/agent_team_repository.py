"""Agent team data access layer."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload

from common.app.models import Agent
from common.app.models import AgentTeam
from common.app.models import AgentTeamMember
from common.app.models import Project
from common.app.models import TeamExecutionType


class AgentTeamRepository:
    """Handles database access for agent teams."""

    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        project_id: UUID,
        execution_type: TeamExecutionType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AgentTeam], int]:
        statement = self._base_statement().where(AgentTeam.project_id == project_id)
        count_statement = select(func.count(AgentTeam.id)).where(AgentTeam.project_id == project_id)
        if execution_type is not None:
            statement = statement.where(AgentTeam.execution_type == execution_type)
            count_statement = count_statement.where(AgentTeam.execution_type == execution_type)
        items = list(
            self.db.scalars(
                statement.order_by(AgentTeam.name.asc()).offset(offset).limit(limit)
            ).unique().all()
        )
        total = self.db.scalar(count_statement) or 0
        return items, total

    def get(self, team_id: UUID) -> AgentTeam | None:
        return self.db.scalar(
            self._base_statement().where(AgentTeam.id == team_id)
        )

    def get_by_slug(self, project_id: UUID, slug: str, exclude_id: UUID | None = None) -> AgentTeam | None:
        stmt = self._base_statement().where(
            AgentTeam.project_id == project_id,
            AgentTeam.slug == slug,
        )
        if exclude_id is not None:
            stmt = stmt.where(AgentTeam.id != exclude_id)
        return self.db.scalar(stmt)

    def add(self, team: AgentTeam) -> None:
        self.db.add(team)
        self.db.flush()

    def delete(self, team: AgentTeam) -> None:
        self.db.delete(team)

    def get_agents_by_ids(self, agent_ids: list[UUID], project_id: UUID) -> list[Agent]:
        if not agent_ids:
            return []
        return list(
            self.db.scalars(
                select(Agent)
                .where(Agent.id.in_(agent_ids), Agent.project_id == project_id)
            ).all()
        )

    def _base_statement(self) -> Select[tuple[AgentTeam]]:
        return select(AgentTeam).options(
            joinedload(AgentTeam.project),
            selectinload(AgentTeam.members).joinedload(AgentTeamMember.agent),
        )
