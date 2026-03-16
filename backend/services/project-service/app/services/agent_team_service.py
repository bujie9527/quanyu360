"""Agent team business logic."""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from fastapi import status

from app.repositories import AgentTeamRepository
from app.schemas.agent_team_schemas import AgentTeamCreateRequest
from app.schemas.agent_team_schemas import AgentTeamMemberInput
from app.schemas.agent_team_schemas import AgentTeamUpdateRequest
from common.app.models import AgentTeam
from common.app.models import AgentTeamMember
from common.app.models import TeamExecutionType


class AgentTeamService:
    """Orchestrates agent team business logic."""

    def __init__(self, repo: AgentTeamRepository):
        self.repo = repo

    def list_teams(
        self,
        project_id: UUID,
        execution_type: TeamExecutionType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AgentTeam], int]:
        return self.repo.list(
            project_id=project_id,
            execution_type=execution_type,
            limit=limit,
            offset=offset,
        )

    def get_team(self, team_id: UUID) -> AgentTeam:
        team = self.repo.get(team_id)
        if team is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent team not found.")
        return team

    def get_team_in_project(self, team_id: UUID, project_id: UUID) -> AgentTeam:
        team = self.get_team(team_id)
        if team.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent team not found.")
        return team

    def create_team(self, project_id: UUID, payload: AgentTeamCreateRequest) -> AgentTeam:
        from common.app.models import Project
        project = self.repo.db.get(Project, project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

        if self.repo.get_by_slug(project_id, payload.slug) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Agent team with slug '{payload.slug}' already exists in this project.",
            )

        team = AgentTeam(
            project_id=project_id,
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            execution_type=payload.execution_type,
        )
        self.repo.add(team)
        self._sync_members(team, payload.members, project_id)
        self.repo.db.commit()
        return self.get_team(team.id)

    def update_team(self, team_id: UUID, project_id: UUID, payload: AgentTeamUpdateRequest) -> AgentTeam:
        team = self.get_team_in_project(team_id, project_id)
        if payload.name is not None:
            team.name = payload.name
        if payload.description is not None:
            team.description = payload.description
        if payload.execution_type is not None:
            team.execution_type = payload.execution_type
        if payload.members is not None:
            self._sync_members(team, payload.members, project_id)
        self.repo.db.commit()
        return self.get_team(team_id)

    def delete_team(self, team_id: UUID, project_id: UUID) -> None:
        team = self.get_team_in_project(team_id, project_id)
        if team.tasks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent team cannot be deleted because tasks are assigned to it.",
            )
        self.repo.delete(team)
        self.repo.db.commit()

    def _sync_members(self, team: AgentTeam, members: list[AgentTeamMemberInput], project_id: UUID) -> None:
        agent_ids = [m.agent_id for m in members]
        agents = self.repo.get_agents_by_ids(agent_ids, project_id)
        agent_map = {a.id: a for a in agents}
        missing = [str(aid) for aid in agent_ids if aid not in agent_map]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agents not found: {', '.join(missing)}",
            )

        for m in list(team.members):
            self.repo.db.delete(m)
        self.repo.db.flush()

        sorted_members = sorted(members, key=lambda x: (x.order_index, str(x.agent_id)))
        for i, inp in enumerate(sorted_members):
            self.repo.db.add(
                AgentTeamMember(
                    team_id=team.id,
                    agent_id=inp.agent_id,
                    role_in_team=inp.role_in_team,
                    order_index=inp.order_index if inp.order_index != 0 else i,
                )
            )
        self.repo.db.flush()
