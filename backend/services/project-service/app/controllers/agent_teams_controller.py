"""Agent team HTTP endpoints."""
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import Response
from fastapi import status

from app.dependencies import get_agent_team_service
from app.dependencies import get_tenant_context_dep
from app.schemas import AgentTeamCreateRequest
from app.schemas import AgentTeamDetailResponse
from app.schemas import AgentTeamListResponse
from app.schemas import AgentTeamMemberResponse
from app.schemas import AgentTeamSummaryResponse
from app.schemas import AgentTeamUpdateRequest
from app.services import AgentTeamService
from common.app.auth import TenantContext
from common.app.models import TeamExecutionType

router = APIRouter()


def _build_member_response(m) -> AgentTeamMemberResponse:
    return AgentTeamMemberResponse(
        id=m.id,
        agent_id=m.agent_id,
        agent_name=m.agent.name if m.agent else "",
        role_in_team=m.role_in_team,
        order_index=m.order_index,
    )


def _build_team_summary(team) -> AgentTeamSummaryResponse:
    return AgentTeamSummaryResponse(
        id=team.id,
        project_id=team.project_id,
        name=team.name,
        slug=team.slug,
        description=team.description,
        execution_type=team.execution_type.value,
        member_count=len(team.members),
        created_at=team.created_at,
        updated_at=team.updated_at,
    )


def _build_team_detail(team) -> AgentTeamDetailResponse:
    return AgentTeamDetailResponse(
        id=team.id,
        project_id=team.project_id,
        name=team.name,
        slug=team.slug,
        description=team.description,
        execution_type=team.execution_type.value,
        members=[_build_member_response(m) for m in sorted(team.members, key=lambda x: (x.order_index, x.id))],
        created_at=team.created_at,
        updated_at=team.updated_at,
    )


@router.post(
    "/projects/{project_id}/agent-teams",
    response_model=AgentTeamDetailResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["agent-teams"],
)
def create_agent_team(
    project_id: UUID,
    payload: AgentTeamCreateRequest,
    service: AgentTeamService = Depends(get_agent_team_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> AgentTeamDetailResponse:
    # Project service would validate project access - for now we delegate to team service
    team = service.create_team(project_id, payload)
    if ctx and team.project.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Project not found.")
    return _build_team_detail(team)


@router.get(
    "/projects/{project_id}/agent-teams",
    response_model=AgentTeamListResponse,
    tags=["agent-teams"],
)
def list_agent_teams(
    project_id: UUID,
    execution_type: TeamExecutionType | None = Query(default=None, alias="execution_type"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: AgentTeamService = Depends(get_agent_team_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> AgentTeamListResponse:
    items, total = service.list_teams(
        project_id=project_id,
        execution_type=execution_type,
        limit=limit,
        offset=offset,
    )
    if items and ctx:
        for t in items:
            if t.project.tenant_id != ctx.tenant_id:
                raise HTTPException(status_code=404, detail="Project not found.")
    return AgentTeamListResponse(items=[_build_team_summary(t) for t in items], total=total)


@router.get(
    "/projects/{project_id}/agent-teams/{team_id}",
    response_model=AgentTeamDetailResponse,
    tags=["agent-teams"],
)
def get_agent_team(
    project_id: UUID,
    team_id: UUID,
    service: AgentTeamService = Depends(get_agent_team_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> AgentTeamDetailResponse:
    team = service.get_team_in_project(team_id, project_id)
    if ctx and team.project.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Project not found.")
    return _build_team_detail(team)


@router.put(
    "/projects/{project_id}/agent-teams/{team_id}",
    response_model=AgentTeamDetailResponse,
    tags=["agent-teams"],
)
def update_agent_team(
    project_id: UUID,
    team_id: UUID,
    payload: AgentTeamUpdateRequest,
    service: AgentTeamService = Depends(get_agent_team_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> AgentTeamDetailResponse:
    team = service.update_team(team_id, project_id, payload)
    if ctx and team.project.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Project not found.")
    return _build_team_detail(team)


@router.delete(
    "/projects/{project_id}/agent-teams/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["agent-teams"],
)
def delete_agent_team(
    project_id: UUID,
    team_id: UUID,
    service: AgentTeamService = Depends(get_agent_team_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> Response:
    team = service.get_team_in_project(team_id, project_id)
    if ctx and team.project.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Project not found.")
    service.delete_team(team_id, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
