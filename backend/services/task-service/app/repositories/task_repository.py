"""Task data access layer."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from common.app.models import Agent
from common.app.models import AgentReflection
from common.app.models import AgentTeam
from common.app.models import AgentTeamMember
from common.app.models import Project
from common.app.models import Task
from common.app.models import TaskPriority
from common.app.models import TaskStatus
from common.app.models import User
from common.app.models import UserStatus
from common.app.models import Workflow


class TaskRepository:
    """Handles database access for tasks."""

    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        project_id: UUID | None = None,
        agent_id: UUID | None = None,
        workflow_id: UUID | None = None,
        status_filter: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Task], int]:
        statement = self._base_statement()
        count_statement = select(func.count(Task.id))
        if project_id is not None:
            statement = statement.where(Task.project_id == project_id)
            count_statement = count_statement.where(Task.project_id == project_id)
        if agent_id is not None:
            statement = statement.where(Task.agent_id == agent_id)
            count_statement = count_statement.where(Task.agent_id == agent_id)
        if workflow_id is not None:
            statement = statement.where(Task.workflow_id == workflow_id)
            count_statement = count_statement.where(Task.workflow_id == workflow_id)
        if status_filter is not None:
            statement = statement.where(Task.status == status_filter)
            count_statement = count_statement.where(Task.status == status_filter)
        if priority is not None:
            statement = statement.where(Task.priority == priority)
            count_statement = count_statement.where(Task.priority == priority)
        if search:
            term = f"%{search.strip()}%"
            pred = or_(Task.title.ilike(term), Task.description.ilike(term))
            statement = statement.where(pred)
            count_statement = count_statement.where(pred)
        items = self.db.scalars(
            statement.order_by(Task.created_at.desc()).offset(offset).limit(limit)
        ).unique().all()
        total = self.db.scalar(count_statement) or 0
        return items, total

    def get(self, task_id: UUID) -> Task | None:
        return self.db.scalar(self._base_statement().where(Task.id == task_id))

    def get_with_team(self, task_id: UUID) -> Task | None:
        """Get task with team and members loaded (for team execution)."""
        stmt = select(Task).options(
            joinedload(Task.project),
            joinedload(Task.agent),
            joinedload(Task.workflow),
            joinedload(Task.created_by),
            joinedload(Task.team).joinedload(AgentTeam.members).joinedload(AgentTeamMember.agent),
        )
        return self.db.scalar(stmt.where(Task.id == task_id))

    def add(self, task: Task) -> None:
        self.db.add(task)

    def get_all_ordered_by_created(self) -> list[Task]:
        return list(self.db.scalars(select(Task).order_by(Task.created_at.asc())).all())

    def get_project(self, project_id: UUID) -> Project | None:
        return self.db.get(Project, project_id)

    def get_agent_in_project(self, agent_id: UUID, project_id: UUID) -> Agent | None:
        return self.db.scalar(
            select(Agent).where(Agent.id == agent_id, Agent.project_id == project_id)
        )

    def get_workflow_in_project(self, workflow_id: UUID, project_id: UUID) -> Workflow | None:
        return self.db.scalar(
            select(Workflow).where(Workflow.id == workflow_id, Workflow.project_id == project_id)
        )

    def get_team_in_project(self, team_id: UUID, project_id: UUID) -> AgentTeam | None:
        return self.db.scalar(
            select(AgentTeam).where(AgentTeam.id == team_id, AgentTeam.project_id == project_id)
        )

    def get_user_in_tenant(self, user_id: UUID, tenant_id: UUID) -> User | None:
        return self.db.scalar(
            select(User).where(
                User.id == user_id,
                User.tenant_id == tenant_id,
                User.status == UserStatus.active,
            )
        )

    def get_recent_reflections_for_agent(self, agent_id: UUID, limit: int = 5) -> list[AgentReflection]:
        """Get recent reflections for an agent to improve next run."""
        stmt = (
            select(AgentReflection)
            .where(AgentReflection.agent_id == agent_id)
            .order_by(AgentReflection.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def _base_statement(self) -> Select[tuple[Task]]:
        return select(Task).options(
            joinedload(Task.project),
            joinedload(Task.agent),
            joinedload(Task.workflow),
            joinedload(Task.created_by),
        )
