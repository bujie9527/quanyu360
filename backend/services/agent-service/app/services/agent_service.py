"""Agent business logic."""
from __future__ import annotations

import re
from uuid import UUID

from fastapi import HTTPException
from fastapi import status

from app.repositories import AgentRepository
from app.schemas.agent_schemas import AgentCreateRequest
from app.schemas.agent_schemas import AgentSkillInput
from app.schemas.agent_schemas import AgentToolAssignmentInput
from app.schemas.agent_schemas import AgentUpdateRequest
from common.app.models import Agent
from common.app.models import AgentSkill
from common.app.models import AgentToolLink
from common.app.models import AgentToolPermission
from common.app.models import AgentWorkflowLink
from common.app.services.tool_permission_service import get_allowed_tool_slugs as _get_allowed_tool_slugs


class AgentService:
    """Orchestrates agent business logic."""

    def __init__(self, repo: AgentRepository):
        self.repo = repo

    def list_agents(
        self,
        project_id: UUID | None = None,
        status_filter=None,  # AgentStatus | None from controller
        role: str | None = None,
        model: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Agent], int]:
        return self.repo.list(
            project_id=project_id,
            status_filter=status_filter,
            role=role,
            model=model,
            search=search,
            limit=limit,
            offset=offset,
        )

    def get_agent(self, agent_id: UUID) -> Agent:
        agent = self.repo.get(agent_id)
        if agent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found.")
        return agent

    def create_agent(self, payload: AgentCreateRequest) -> Agent:
        project = self.repo.get_project(payload.project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        created_by = (
            self.repo.get_user_in_tenant(payload.created_by_user_id, project.tenant_id)
            if payload.created_by_user_id
            else None
        )
        slug = self._generate_slug(project.id, payload.name)
        agent = Agent(
            project_id=project.id,
            created_by=created_by,
            name=payload.name,
            slug=slug,
            role=payload.role,
            role_title=payload.role_title or self._humanize_role(payload.role),
            model=payload.model,
            system_prompt=payload.system_prompt,
            status=payload.status,
            max_concurrency=payload.max_concurrency,
            config=payload.config,
        )
        self.repo.add(agent)
        self._sync_skills(agent, payload.skills)
        self._sync_tools(agent, payload.tools)
        self._sync_workflows(agent, payload.workflow_ids)
        self.repo.db.commit()
        return self.get_agent(agent.id)

    def update_agent(self, agent_id: UUID, payload: AgentUpdateRequest) -> Agent:
        agent = self.get_agent(agent_id)
        if "project_id" in payload.model_fields_set and payload.project_id and payload.project_id != agent.project_id:
            self._reassign_project(agent, payload.project_id)
        if "name" in payload.model_fields_set and payload.name:
            agent.name = payload.name
            agent.slug = self._generate_slug(agent.project_id, payload.name, exclude_agent_id=agent.id)
        if "role" in payload.model_fields_set and payload.role:
            agent.role = payload.role
            if "role_title" not in payload.model_fields_set or not payload.role_title:
                agent.role_title = self._humanize_role(payload.role)
        if "role_title" in payload.model_fields_set and payload.role_title is not None:
            agent.role_title = payload.role_title
        if "model" in payload.model_fields_set and payload.model:
            agent.model = payload.model
        if "system_prompt" in payload.model_fields_set and payload.system_prompt is not None:
            agent.system_prompt = payload.system_prompt
        if "max_concurrency" in payload.model_fields_set and payload.max_concurrency is not None:
            agent.max_concurrency = payload.max_concurrency
        if "status" in payload.model_fields_set and payload.status is not None:
            agent.status = payload.status
        if "config" in payload.model_fields_set and payload.config is not None:
            agent.config = payload.config
        if payload.skills is not None:
            self._sync_skills(agent, payload.skills)
        if payload.tools is not None:
            self._sync_tools(agent, payload.tools)
        if payload.workflow_ids is not None:
            self._sync_workflows(agent, payload.workflow_ids)
        self.repo.db.commit()
        return self.get_agent(agent.id)

    def delete_agent(self, agent_id: UUID) -> None:
        agent = self.get_agent(agent_id)
        if self.repo.has_tasks(agent.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Agent cannot be deleted because tasks are assigned to it.",
            )
        self.repo.delete(agent)
        self.repo.db.commit()

    def _sync_skills(self, agent: Agent, skills: list[AgentSkillInput]) -> None:
        existing_by_name = {s.name.lower(): s for s in agent.skills}
        desired_names = {s.name.lower() for s in skills}
        for skill in list(agent.skills):
            if skill.name.lower() not in desired_names:
                self.repo.db.delete(skill)
        for p in skills:
            key = p.name.lower()
            existing = existing_by_name.get(key)
            if existing is None:
                self.repo.db.add(
                    AgentSkill(
                        agent=agent,
                        name=p.name,
                        category=p.category,
                        proficiency_level=p.proficiency_level,
                        description=p.description,
                        is_core=p.is_core,
                    )
                )
            else:
                existing.category = p.category
                existing.proficiency_level = p.proficiency_level
                existing.description = p.description
                existing.is_core = p.is_core
        self.repo.db.flush()

    def _sync_tools(self, agent: Agent, tools: list[AgentToolAssignmentInput]) -> None:
        desired = {t.tool_id: t for t in tools}
        existing = {l.tool_id: l for l in agent.tool_links}
        if desired:
            found = self.repo.get_tools_by_ids(list(desired.keys()))
            found_map = {t.id: t for t in found}
            missing = [str(i) for i in desired if i not in found_map]
            if missing:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tools not found: {', '.join(missing)}")
            for tool in found:
                if tool.project_id != agent.project_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Tool '{tool.name}' does not belong to the agent project.",
                    )
        for tid, link in list(existing.items()):
            if tid not in desired:
                self.repo.db.delete(link)
        for tid, p in desired.items():
            if tid not in existing:
                self.repo.db.add(
                    AgentToolLink(
                        agent=agent,
                        tool_id=tid,
                        is_enabled=p.is_enabled,
                        invocation_timeout_seconds=p.invocation_timeout_seconds,
                    )
                )
            else:
                existing[tid].is_enabled = p.is_enabled
                existing[tid].invocation_timeout_seconds = p.invocation_timeout_seconds
        self.repo.db.flush()

    def _sync_workflows(self, agent: Agent, workflow_ids: list[UUID]) -> None:
        desired = set(workflow_ids)
        existing = {l.workflow_id: l for l in agent.workflow_links}
        if desired:
            found = self.repo.get_workflows_by_ids(list(desired))
            found_map = {w.id: w for w in found}
            missing = [str(i) for i in desired if i not in found_map]
            if missing:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflows not found: {', '.join(missing)}")
            for w in found:
                if w.project_id != agent.project_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Workflow '{w.name}' does not belong to the agent project.",
                    )
        for wid, link in list(existing.items()):
            if wid not in desired:
                self.repo.db.delete(link)
        for wid in desired:
            if wid not in existing:
                self.repo.db.add(AgentWorkflowLink(agent=agent, workflow_id=wid))
        self.repo.db.flush()

    def _reassign_project(self, agent: Agent, project_id: UUID) -> None:
        target = self.repo.get_project(project_id)
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        if target.tenant_id != agent.project.tenant_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agent cannot be moved to a project in another tenant.")
        if self.repo.has_tasks(agent.id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Agent cannot be moved because it already has tasks.")
        agent.project_id = target.id
        agent.workflow_links.clear()
        agent.tool_links.clear()
        self.repo.db.flush()

    def _generate_slug(self, project_id: UUID, name: str, exclude_agent_id: UUID | None = None) -> str:
        base = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-") or "agent"
        candidate = base[:120]
        suffix = 1
        while self.repo.slug_exists(project_id, candidate, exclude_agent_id):
            suffix += 1
            candidate = f"{base[:110]}-{suffix}"[:120]
        return candidate

    @staticmethod
    def _humanize_role(role: str) -> str:
        return role.replace("_", " ").strip().title()

    def get_allowed_tool_slugs(self, agent_id: UUID) -> list[str] | None:
        """Get tool slugs agent can use. None = no restrictions (allow all)."""
        return _get_allowed_tool_slugs(self.repo.db, agent_id)

    def add_tool_permission(self, agent_id: UUID, tool_slug: str) -> AgentToolPermission:
        """Grant agent permission to use tool by slug."""
        self.get_agent(agent_id)
        slug = tool_slug.strip().lower()
        from sqlalchemy import select

        existing = self.repo.db.scalar(
            select(AgentToolPermission).where(
                AgentToolPermission.agent_id == agent_id,
                AgentToolPermission.tool_slug == slug,
            )
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Agent already has permission for tool '{tool_slug}'.",
            )
        perm = AgentToolPermission(agent_id=agent_id, tool_slug=slug)
        self.repo.db.add(perm)
        self.repo.db.commit()
        self.repo.db.refresh(perm)
        return perm

    def remove_tool_permission(self, agent_id: UUID, tool_slug: str) -> None:
        """Revoke agent permission to use tool by slug."""
        self.get_agent(agent_id)
        slug = tool_slug.strip().lower()
        from sqlalchemy import delete

        stmt = delete(AgentToolPermission).where(
            AgentToolPermission.agent_id == agent_id,
            AgentToolPermission.tool_slug == slug,
        )
        self.repo.db.execute(stmt)
        self.repo.db.commit()
