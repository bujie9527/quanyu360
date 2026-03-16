"""AgentTemplate business logic."""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from fastapi import status

from app.repositories.agent_template_repository import AgentTemplateRepository
from app.schemas.agent_template_schemas import AgentTemplateCreateRequest
from app.schemas.agent_template_schemas import AgentTemplateUpdateRequest
from common.app.models import AgentTemplate


class AgentTemplateService:
    def __init__(self, repo: AgentTemplateRepository):
        self.repo = repo

    def list(self, enabled: bool | None = None, limit: int = 50, offset: int = 0) -> tuple[list[AgentTemplate], int]:
        return self.repo.list(enabled=enabled, limit=limit, offset=offset)

    def list_templates(
        self,
        enabled: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AgentTemplate], int]:
        return self.list(enabled=enabled, limit=limit, offset=offset)

    def get(self, template_id: UUID) -> AgentTemplate:
        return self.get_template(template_id)

    def get_template(self, template_id: UUID) -> AgentTemplate:
        t = self.repo.get(template_id)
        if t is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AgentTemplate not found.")
        return t

    def create_template(self, payload: AgentTemplateCreateRequest) -> AgentTemplate:
        template = AgentTemplate(
            name=payload.name,
            description=payload.description,
            system_prompt=payload.system_prompt,
            model=payload.model,
            default_tools=payload.default_tools,
            default_workflows=payload.default_workflows,
            config_schema=payload.config_schema,
            enabled=payload.enabled,
        )
        self.repo.add(template)
        self.repo.db.commit()
        self.repo.db.refresh(template)
        return template

    def update_template(self, template_id: UUID, payload: AgentTemplateUpdateRequest) -> AgentTemplate:
        template = self.get_template(template_id)
        if payload.name is not None:
            template.name = payload.name
        if payload.description is not None:
            template.description = payload.description
        if payload.system_prompt is not None:
            template.system_prompt = payload.system_prompt
        if payload.model is not None:
            template.model = payload.model
        if payload.default_tools is not None:
            template.default_tools = payload.default_tools
        if payload.default_workflows is not None:
            template.default_workflows = payload.default_workflows
        if payload.config_schema is not None:
            template.config_schema = payload.config_schema
        if payload.enabled is not None:
            template.enabled = payload.enabled
        self.repo.db.commit()
        self.repo.db.refresh(template)
        return template

    def delete_template(self, template_id: UUID) -> None:
        template = self.get_template(template_id)
        self.repo.delete(template)
        self.repo.db.commit()
