"""AgentTemplate HTTP endpoints."""
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from fastapi import status

from app.dependencies import get_agent_template_service
from app.dependencies import require_platform_admin
from app.schemas.agent_template_schemas import (
    AgentTemplateCreateRequest,
    AgentTemplateDetailResponse,
    AgentTemplateListResponse,
    AgentTemplateUpdateRequest,
)
from app.services.agent_template_service import AgentTemplateService

router = APIRouter(prefix="/agent/templates", tags=["agent-templates"])


def _to_detail(t) -> AgentTemplateDetailResponse:
    return AgentTemplateDetailResponse(
        id=t.id,
        name=t.name,
        description=t.description,
        model=t.model,
        default_tools=t.default_tools or [],
        default_workflows=t.default_workflows or [],
        system_prompt=t.system_prompt or "",
        enabled=t.enabled,
    )


@router.get("", response_model=AgentTemplateListResponse)
def list_templates(
    enabled: bool | None = None,
    limit: int = 50,
    offset: int = 0,
    service: AgentTemplateService = Depends(get_agent_template_service),
) -> AgentTemplateListResponse:
    items, total = service.list(enabled=enabled, limit=limit, offset=offset)
    return AgentTemplateListResponse(
        items=[_to_detail(t) for t in items],
        total=total,
    )


@router.get("/{template_id}", response_model=AgentTemplateDetailResponse)
def get_template_detail(
    template_id: UUID,
    service: AgentTemplateService = Depends(get_agent_template_service),
) -> AgentTemplateDetailResponse:
    t = service.get(template_id)
    return _to_detail(t)


@router.post("", response_model=AgentTemplateDetailResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    payload: AgentTemplateCreateRequest,
    request: Request,
    service: AgentTemplateService = Depends(get_agent_template_service),
) -> AgentTemplateDetailResponse:
    require_platform_admin(request)
    t = service.create_template(payload)
    return _to_detail(t)


@router.put("/{template_id}", response_model=AgentTemplateDetailResponse)
def update_template(
    template_id: UUID,
    payload: AgentTemplateUpdateRequest,
    service: AgentTemplateService = Depends(get_agent_template_service),
) -> AgentTemplateDetailResponse:
    t = service.update_template(template_id, payload)
    return _to_detail(t)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: UUID,
    service: AgentTemplateService = Depends(get_agent_template_service),
) -> Response:
    service.delete_template(template_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
