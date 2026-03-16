"""Project business logic."""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from fastapi import status

from app.repositories import ProjectRepository
from app.schemas.project_schemas import ProjectCreateRequest
from app.schemas.project_schemas import ProjectTeamMemberInput
from app.schemas.project_schemas import ProjectUpdateRequest
from common.app.audit import log_audit
from common.app.models import AuditAction
from common.app.models import Project
from common.app.models import ProjectStatus
from common.app.models import ProjectTeamMember
from common.app.models import UserRole


class ProjectService:
    """Orchestrates project business logic."""

    def __init__(self, repo: ProjectRepository):
        self.repo = repo

    def list_projects(
        self,
        tenant_id: UUID | None = None,
        owner_id: UUID | None = None,
        status_filter: ProjectStatus | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Project], int]:
        return self.repo.list(
            tenant_id=tenant_id,
            owner_id=owner_id,
            status_filter=status_filter,
            search=search,
            limit=limit,
            offset=offset,
        )

    def get_project(self, project_id: UUID) -> Project:
        project = self.repo.get(project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        return project

    def create_project(self, payload: ProjectCreateRequest, actor_user_id: UUID | None = None) -> Project:
        tenant = self.repo.get_tenant(payload.tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found.")

        owner = self.repo.get_user_in_tenant(payload.owner_id, tenant.id) if payload.owner_id else None
        key = self.repo.generate_project_key(payload.tenant_id, payload.name)

        project = Project(
            tenant_id=tenant.id,
            owner=owner,
            key=key,
            name=payload.name,
            description=payload.description,
            status=ProjectStatus.draft,
            project_type=payload.project_type,
            matrix_config=payload.matrix_config or {},
        )
        self.repo.add(project)

        self._sync_team_members(project, payload.team_members, owner.id if owner else None)
        self._attach_agents(project, payload.agent_ids)
        self._attach_workflows(project, payload.workflow_ids)

        log_audit(
            self.repo.db,
            tenant_id=tenant.id,
            action=AuditAction.create,
            entity_type="project",
            entity_id=project.id,
            project_id=project.id,
            actor_user_id=actor_user_id,
            payload={"name": project.name, "key": project.key},
        )
        self.repo.db.commit()
        return self.get_project(project.id)

    def update_project(
        self, project_id: UUID, payload: ProjectUpdateRequest, actor_user_id: UUID | None = None
    ) -> Project:
        project = self.get_project(project_id)

        if "name" in payload.model_fields_set and payload.name is not None:
            project.name = payload.name
        if "description" in payload.model_fields_set:
            project.description = payload.description
        if "status" in payload.model_fields_set and payload.status is not None:
            project.status = payload.status
        if "project_type" in payload.model_fields_set and payload.project_type is not None:
            project.project_type = payload.project_type
        if "matrix_config" in payload.model_fields_set and payload.matrix_config is not None:
            project.matrix_config = payload.matrix_config
        if "owner_id" in payload.model_fields_set:
            project.owner = (
                self.repo.get_user_in_tenant(payload.owner_id, project.tenant_id)
                if payload.owner_id
                else None
            )

        owner_id = project.owner_user_id
        if payload.team_members is not None:
            self._sync_team_members(project, payload.team_members, owner_id)
        elif owner_id is not None:
            self._ensure_owner_membership(project, owner_id)

        if payload.agent_ids:
            self._attach_agents(project, payload.agent_ids)
        if payload.workflow_ids:
            self._attach_workflows(project, payload.workflow_ids)

        log_audit(
            self.repo.db,
            tenant_id=project.tenant_id,
            action=AuditAction.update,
            entity_type="project",
            entity_id=project.id,
            project_id=project.id,
            actor_user_id=actor_user_id,
            payload={"name": project.name},
        )
        self.repo.db.commit()
        return self.get_project(project.id)

    def delete_project(self, project_id: UUID, actor_user_id: UUID | None = None) -> None:
        project = self.get_project(project_id)
        log_audit(
            self.repo.db,
            tenant_id=project.tenant_id,
            action=AuditAction.delete,
            entity_type="project",
            entity_id=project.id,
            project_id=project.id,
            actor_user_id=actor_user_id,
            payload={"name": project.name, "key": project.key},
        )
        self.repo.delete(project)
        self.repo.db.commit()

    def _sync_team_members(
        self,
        project: Project,
        team_members: list[ProjectTeamMemberInput],
        owner_id: UUID | None,
    ) -> None:
        desired_members: dict[UUID, UserRole] = {}
        for member in team_members:
            user = self.repo.get_user_in_tenant(member.user_id, project.tenant_id)
            if user is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in tenant.")
            desired_members[user.id] = member.role

        if owner_id is not None:
            if self.repo.get_user_in_tenant(owner_id, project.tenant_id) is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in tenant.")
            desired_members[owner_id] = UserRole.admin

        existing = {m.user_id: m for m in project.team_memberships}

        for user_id, membership in list(existing.items()):
            if user_id not in desired_members:
                self.repo.db.delete(membership)

        for user_id, role in desired_members.items():
            membership = existing.get(user_id)
            if membership is None:
                self.repo.db.add(ProjectTeamMember(project=project, user_id=user_id, role=role))
            else:
                membership.role = role

        self.repo.db.flush()

    def _ensure_owner_membership(self, project: Project, owner_id: UUID) -> None:
        for membership in project.team_memberships:
            if membership.user_id == owner_id:
                membership.role = UserRole.admin
                self.repo.db.flush()
                return
        self.repo.db.add(ProjectTeamMember(project=project, user_id=owner_id, role=UserRole.admin))
        self.repo.db.flush()

    def _attach_agents(self, project: Project, agent_ids: list[UUID]) -> None:
        if not agent_ids:
            return
        agents = self.repo.get_agents_by_ids(agent_ids)
        found_ids = {a.id for a in agents}
        missing = [str(i) for i in agent_ids if i not in found_ids]
        if missing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agents not found: {', '.join(missing)}")

        for agent in agents:
            if agent.project.tenant_id != project.tenant_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agent belongs to a different tenant.")
            if agent.project_id != project.id and agent.tasks:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Agent '{agent.name}' cannot be moved because it already has tasks.",
                )
            agent.project_id = project.id
        self.repo.db.flush()

    def _attach_workflows(self, project: Project, workflow_ids: list[UUID]) -> None:
        if not workflow_ids:
            return
        workflows = self.repo.get_workflows_by_ids(workflow_ids)
        found_ids = {w.id for w in workflows}
        missing = [str(i) for i in workflow_ids if i not in found_ids]
        if missing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflows not found: {', '.join(missing)}")

        for workflow in workflows:
            if workflow.project.tenant_id != project.tenant_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workflow belongs to a different tenant.")
            if workflow.project_id != project.id and workflow.tasks:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Workflow '{workflow.name}' cannot be moved because it already has tasks.",
                )
            workflow.project_id = project.id
        self.repo.db.flush()
