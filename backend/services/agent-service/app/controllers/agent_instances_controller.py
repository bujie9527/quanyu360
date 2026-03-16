"""AgentInstance HTTP endpoints."""
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Response
from fastapi import status

from app.dependencies import get_agent_instance_service
from app.schemas.agent_instance_schemas import (
    AgentInstanceCreateRequest,
    AgentInstanceDetailResponse,
    AgentInstanceListResponse,
    AgentInstanceUpdateRequest,
)
from app.services.agent_instance_service import AgentInstanceService

router = APIRouter(prefix="/agent/instances", tags=["agent-instances"])


def _to_detail(inst) -> AgentInstanceDetailResponse:
    effective_tools = (
        list(inst.tools_override) if inst.tools_override
        else (_get_template_default_tools(inst) if inst.template else [])
    )
    effective_workflows = _get_template_default_workflows(inst) if inst.template else []
    created_at = inst.created_at.isoformat() if getattr(inst, "created_at", None) else None
    return AgentInstanceDetailResponse(
        id=inst.id,
        tenant_id=inst.tenant_id,
        project_id=inst.project_id,
        template_id=inst.template_id,
        name=inst.name,
        description=inst.description,
        system_prompt=inst.system_prompt or "",
        model=inst.model or "gpt-4",
        default_tools=effective_tools,
        default_workflows=effective_workflows,
        tools_override=inst.tools_override or [],
        knowledge_base_id=inst.knowledge_base_id,
        config=inst.config or {},
        enabled=inst.enabled,
        created_at=created_at,
        template_name=inst.template.name if getattr(inst, "template", None) and inst.template else None,
        project_name=inst.project.name if getattr(inst, "project", None) and inst.project else None,
        knowledge_base_name=inst.knowledge_base.name if getattr(inst, "knowledge_base", None) and inst.knowledge_base else None,
    )


def _get_template_default_tools(inst) -> list[str]:
    if getattr(inst, "template", None) and inst.template and inst.template.default_tools:
        return list(inst.template.default_tools)
    return []


def _get_template_default_workflows(inst) -> list[str]:
    if getattr(inst, "template", None) and inst.template and inst.template.default_workflows:
        return list(inst.template.default_workflows)
    return []


@router.post("", response_model=AgentInstanceDetailResponse, status_code=status.HTTP_201_CREATED)
def create_instance(
    payload: AgentInstanceCreateRequest,
    service: AgentInstanceService = Depends(get_agent_instance_service),
) -> AgentInstanceDetailResponse:
    inst = service.create(payload)
    return _to_detail(inst)


@router.get("", response_model=AgentInstanceListResponse)
def list_instances(
    project_id: UUID | None = Query(default=None),
    template_id: UUID | None = Query(default=None),
    enabled: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: AgentInstanceService = Depends(get_agent_instance_service),
) -> AgentInstanceListResponse:
    items, total = service.list(
        project_id=project_id,
        template_id=template_id,
        enabled=enabled,
        limit=limit,
        offset=offset,
    )
    return AgentInstanceListResponse(
        items=[_to_detail(i) for i in items],
        total=total,
    )


@router.get("/{instance_id}", response_model=AgentInstanceDetailResponse)
def get_instance(
    instance_id: UUID,
    service: AgentInstanceService = Depends(get_agent_instance_service),
) -> AgentInstanceDetailResponse:
    inst = service.get(instance_id)
    return _to_detail(inst)


@router.put("/{instance_id}", response_model=AgentInstanceDetailResponse)
def update_instance(
    instance_id: UUID,
    payload: AgentInstanceUpdateRequest,
    service: AgentInstanceService = Depends(get_agent_instance_service),
) -> AgentInstanceDetailResponse:
    inst = service.update(instance_id, payload)
    return _to_detail(inst)


@router.delete("/{instance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_instance(
    instance_id: UUID,
    service: AgentInstanceService = Depends(get_agent_instance_service),
) -> Response:
    service.delete(instance_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
