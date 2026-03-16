"""AgentInstance business logic."""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from fastapi import status

from app.repositories.agent_instance_repository import AgentInstanceRepository
from app.schemas.agent_instance_schemas import AgentInstanceCreateRequest
from app.schemas.agent_instance_schemas import AgentInstanceUpdateRequest
from common.app.models import AgentInstance
from common.app.models import AgentTemplate


class AgentInstanceService:
    def __init__(self, repo: AgentInstanceRepository):
        self.repo = repo

    def create(self, payload: AgentInstanceCreateRequest) -> AgentInstance:
        """从 AgentTemplate 复制配置，创建 Agent Instance。"""
        template = self.repo.get_template(payload.template_id)
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AgentTemplate not found.",
            )
        if not template.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="AgentTemplate is disabled.",
            )
        project = self.repo.get_project(payload.project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found.",
            )
        tenant_id = project.tenant_id
        instance = AgentInstance(
            tenant_id=tenant_id,
            project_id=payload.project_id,
            template_id=payload.template_id,
            name=payload.name,
            description=payload.description or template.description,
            system_prompt=template.system_prompt or "",
            model=template.model or "gpt-4",
            tools_override=[],
            knowledge_base_id=None,
            config=dict(template.config_schema or {}),
            enabled=True,
        )
        self.repo.add(instance)
        self.repo.db.commit()
        self.repo.db.refresh(instance)
        return instance

    def list(
        self,
        project_id: UUID | None = None,
        tenant_id: UUID | None = None,
        template_id: UUID | None = None,
        enabled: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AgentInstance], int]:
        return self.repo.list(
            project_id=project_id,
            tenant_id=tenant_id,
            template_id=template_id,
            enabled=enabled,
            limit=limit,
            offset=offset,
        )

    def get(self, instance_id: UUID) -> AgentInstance:
        inst = self.repo.get(instance_id)
        if inst is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AgentInstance not found.",
            )
        return inst

    def update(self, instance_id: UUID, payload: AgentInstanceUpdateRequest) -> AgentInstance:
        inst = self.get(instance_id)
        if payload.name is not None:
            inst.name = payload.name
        if payload.description is not None:
            inst.description = payload.description
        if payload.system_prompt is not None:
            inst.system_prompt = payload.system_prompt
        if payload.model is not None:
            inst.model = payload.model
        if payload.tools_override is not None:
            inst.tools_override = payload.tools_override
        if payload.knowledge_base_id is not None:
            inst.knowledge_base_id = payload.knowledge_base_id
        if payload.config is not None:
            inst.config = payload.config
        if payload.enabled is not None:
            inst.enabled = payload.enabled
        self.repo.db.commit()
        self.repo.db.refresh(inst)
        return inst

    def delete(self, instance_id: UUID) -> None:
        inst = self.get(instance_id)
        self.repo.delete(inst)
        self.repo.db.commit()
