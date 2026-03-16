"""Agent HTTP endpoints."""
from uuid import UUID

import httpx
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Response
from fastapi import status

from app.config import settings
from app.dependencies import get_agent_instance_service
from app.dependencies import get_agent_service
from app.schemas import AgentCreateRequest
from app.schemas import AgentDetailResponse
from app.schemas import AgentListResponse
from app.schemas.agent_instance_schemas import AgentInstanceCreateRequest
from app.schemas.agent_instance_schemas import AgentInstanceDetailResponse
from app.schemas import AgentSkillResponse
from app.schemas import AgentSummaryResponse
from app.schemas import AgentAllowedToolsResponse
from app.schemas import AgentToolPermissionCreate
from app.schemas import AgentToolPermissionResponse
from app.schemas import AgentToolResponse
from app.schemas import AgentUpdateRequest
from app.schemas import AgentWorkflowResponse
from app.services import AgentService
from app.services.agent_instance_service import AgentInstanceService
from common.app.models import Agent
from common.app.models import AgentStatus
from common.app.models import AgentToolLink
from common.app.models import AgentToolPermission
from common.app.models import AgentWorkflowLink

router = APIRouter()


def _build_agent_summary(agent: Agent) -> AgentSummaryResponse:
    return AgentSummaryResponse(
        id=agent.id,
        project_id=agent.project_id,
        name=agent.name,
        role=agent.role,
        role_title=agent.role_title,
        model=agent.model,
        status=agent.status.value,
        skill_count=len(agent.skills),
        tool_count=len(agent.tool_links),
        workflow_count=len(agent.workflow_links),
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


def _build_agent_detail(agent: Agent) -> AgentDetailResponse:
    return AgentDetailResponse(
        id=agent.id,
        project_id=agent.project_id,
        created_by_user_id=agent.created_by_user_id,
        name=agent.name,
        slug=agent.slug,
        role=agent.role,
        role_title=agent.role_title,
        model=agent.model,
        system_prompt=agent.system_prompt,
        status=agent.status.value,
        max_concurrency=agent.max_concurrency,
        config=agent.config,
        skills=[
            AgentSkillResponse(
                id=s.id,
                name=s.name,
                category=s.category,
                proficiency_level=s.proficiency_level,
                description=s.description,
                is_core=s.is_core,
            )
            for s in sorted(agent.skills, key=lambda x: x.name.lower())
        ],
        tools=[
            AgentToolResponse(
                id=link.tool.id,
                name=link.tool.name,
                slug=link.tool.slug,
                tool_type=link.tool.tool_type.value,
                is_enabled=link.is_enabled,
                invocation_timeout_seconds=link.invocation_timeout_seconds,
            )
            for link in sorted(agent.tool_links, key=lambda x: x.tool.name.lower())
        ],
        tool_permissions=[
            AgentToolPermissionResponse(id=p.id, tool_slug=p.tool_slug)
            for p in sorted(agent.tool_permissions or [], key=lambda x: x.tool_slug.lower())
        ],
        workflows=[
            AgentWorkflowResponse(
                id=link.workflow.id,
                name=link.workflow.name,
                slug=link.workflow.slug,
                status=link.workflow.status.value,
                version=link.workflow.version,
            )
            for link in sorted(agent.workflow_links, key=lambda x: x.workflow.name.lower())
        ],
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


@router.post("/agents", response_model=AgentDetailResponse, status_code=status.HTTP_201_CREATED, tags=["agents"])
def create_agent(
    payload: AgentCreateRequest,
    agent_service: AgentService = Depends(get_agent_service),
) -> AgentDetailResponse:
    agent = agent_service.create_agent(payload)
    return _build_agent_detail(agent)


def _instance_to_detail(inst) -> AgentInstanceDetailResponse:
    """Build AgentInstanceDetailResponse from AgentInstance (template 需已加载)."""
    effective_tools = list(inst.tools_override) if inst.tools_override else (
        list(inst.template.default_tools) if inst.template and inst.template.default_tools else []
    )
    effective_workflows = list(inst.template.default_workflows) if inst.template and inst.template.default_workflows else []
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
    )


@router.post("/agents/from-template", response_model=AgentInstanceDetailResponse, status_code=status.HTTP_201_CREATED, tags=["agents"])
def create_agent_from_template(
    payload: AgentInstanceCreateRequest,
    agent_instance_service: AgentInstanceService = Depends(get_agent_instance_service),
) -> AgentInstanceDetailResponse:
    """从 AgentTemplate 复制配置创建 Agent Instance。"""
    inst = agent_instance_service.create(payload)
    return _instance_to_detail(inst)


@router.get("/agents", response_model=AgentListResponse, tags=["agents"])
def list_agents(
    project_id: UUID | None = Query(default=None),
    status_filter: AgentStatus | None = Query(default=None, alias="status"),
    role: str | None = Query(default=None, min_length=2, max_length=120),
    model: str | None = Query(default=None, min_length=2, max_length=120),
    search: str | None = Query(default=None, min_length=1, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    agent_service: AgentService = Depends(get_agent_service),
) -> AgentListResponse:
    items, total = agent_service.list_agents(
        project_id=project_id,
        status_filter=status_filter,
        role=role,
        model=model,
        search=search,
        limit=limit,
        offset=offset,
    )
    return AgentListResponse(
        items=[_build_agent_summary(a) for a in items],
        total=total,
    )


@router.get("/agents/{agent_id}", response_model=AgentDetailResponse, tags=["agents"])
def get_agent(
    agent_id: UUID,
    agent_service: AgentService = Depends(get_agent_service),
) -> AgentDetailResponse:
    agent = agent_service.get_agent(agent_id)
    return _build_agent_detail(agent)


@router.put("/agents/{agent_id}", response_model=AgentDetailResponse, tags=["agents"])
def update_agent(
    agent_id: UUID,
    payload: AgentUpdateRequest,
    agent_service: AgentService = Depends(get_agent_service),
) -> AgentDetailResponse:
    agent = agent_service.update_agent(agent_id, payload)
    return _build_agent_detail(agent)


@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["agents"])
def delete_agent(
    agent_id: UUID,
    agent_service: AgentService = Depends(get_agent_service),
) -> Response:
    agent_service.delete_agent(agent_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/agents/{agent_id}/run", tags=["agents"])
def run_agent(
    agent_id: UUID,
    payload: dict,
) -> dict:
    """
    统一执行接口，代理到 agent-runtime。
    输入: { "type": "workflow|task|chat", "id": "...", "input": {} }
    chat → LLM; workflow → WorkflowEngine; task → TaskTemplate
    """
    base_url = (settings.agent_runtime_url or "").rstrip("/")
    if not base_url:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Agent runtime is not configured.")
    url = f"{base_url}/api/v1/agents/{agent_id}/run"
    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, json=payload, headers={"Content-Type": "application/json"})
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text[:500] if e.response.text else str(e),
        ) from e
    except httpx.RequestError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"Agent runtime unreachable: {e!s}") from e


@router.get("/agents/{agent_id}/allowed-tools", response_model=AgentAllowedToolsResponse, tags=["agents", "tools"])
def get_agent_allowed_tools(
    agent_id: UUID,
    agent_service: AgentService = Depends(get_agent_service),
) -> AgentAllowedToolsResponse:
    """Get tool slugs the agent is allowed to use. unrestricted=True means no restrictions (allow all)."""
    slugs = agent_service.get_allowed_tool_slugs(agent_id)
    return AgentAllowedToolsResponse(
        agent_id=agent_id,
        allowed_tool_slugs=slugs if slugs is not None else [],
        unrestricted=slugs is None,
    )


@router.post("/agents/{agent_id}/tool-permissions", response_model=AgentToolPermissionResponse, status_code=status.HTTP_201_CREATED, tags=["agents", "tools"])
def add_agent_tool_permission(
    agent_id: UUID,
    payload: AgentToolPermissionCreate,
    agent_service: AgentService = Depends(get_agent_service),
) -> AgentToolPermissionResponse:
    """Grant agent permission to use a tool by slug (e.g. wordpress, facebook, seo)."""
    perm = agent_service.add_tool_permission(agent_id, payload.tool_slug)
    return AgentToolPermissionResponse(id=perm.id, tool_slug=perm.tool_slug)


@router.delete("/agents/{agent_id}/tool-permissions/{tool_slug}", status_code=status.HTTP_204_NO_CONTENT, tags=["agents", "tools"])
def remove_agent_tool_permission(
    agent_id: UUID,
    tool_slug: str,
    agent_service: AgentService = Depends(get_agent_service),
) -> Response:
    """Revoke agent permission to use a tool."""
    agent_service.remove_tool_permission(agent_id, tool_slug)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
