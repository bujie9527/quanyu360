"""Project HTTP endpoints."""
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import Response
from fastapi import status

from app.dependencies import get_project_service
from app.dependencies import get_tenant_context_dep
from app.schemas import ProjectAgentResponse
from app.schemas import ProjectCreateRequest
from app.schemas import ProjectDetailResponse
from app.schemas import ProjectListResponse
from app.schemas import ProjectSummaryResponse
from app.schemas import ProjectTaskResponse
from app.schemas import ProjectUpdateRequest
from app.schemas import ProjectWorkflowResponse
from app.schemas import TeamMemberResponse
from app.services import ProjectService
from common.app.auth import TenantContext
from common.app.models import Project
from common.app.models import ProjectStatus

router = APIRouter()


def _build_team_members(project: Project) -> list[TeamMemberResponse]:
    memberships = sorted(project.team_memberships, key=lambda m: (m.user.full_name.lower(), m.created_at))
    return [
        TeamMemberResponse(
            user_id=m.user_id,
            email=m.user.email,
            full_name=m.user.full_name,
            role=m.role,
        )
        for m in memberships
    ]


def _build_project_summary(project: Project) -> ProjectSummaryResponse:
    return ProjectSummaryResponse(
        id=project.id,
        tenant_id=project.tenant_id,
        key=project.key,
        name=project.name,
        description=project.description,
        owner_id=project.owner_user_id,
        status=project.status.value,
        project_type=project.project_type.value,
        matrix_config=project.matrix_config or {},
        team_members=_build_team_members(project),
        agent_count=len(project.agents),
        task_count=len(project.tasks),
        workflow_count=len(project.workflows),
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def _build_project_detail(project: Project) -> ProjectDetailResponse:
    return ProjectDetailResponse(
        id=project.id,
        tenant_id=project.tenant_id,
        key=project.key,
        name=project.name,
        description=project.description,
        owner_id=project.owner_user_id,
        status=project.status.value,
        project_type=project.project_type.value,
        matrix_config=project.matrix_config or {},
        team_members=_build_team_members(project),
        agents=[
            ProjectAgentResponse(
                id=a.id,
                name=a.name,
                slug=a.slug,
                status=a.status.value,
                model=a.model,
            )
            for a in sorted(project.agents, key=lambda x: x.name.lower())
        ],
        tasks=[
            ProjectTaskResponse(
                id=t.id,
                title=t.title,
                status=t.status.value,
                priority=t.priority.value,
                agent_id=t.agent_id,
                workflow_id=t.workflow_id,
            )
            for t in sorted(project.tasks, key=lambda x: x.created_at, reverse=True)
        ],
        workflows=[
            ProjectWorkflowResponse(
                id=w.id,
                name=w.name,
                slug=w.slug,
                status=w.status.value,
                version=w.version,
            )
            for w in sorted(project.workflows, key=lambda x: x.name.lower())
        ],
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("/projects", response_model=ProjectDetailResponse, status_code=status.HTTP_201_CREATED, tags=["projects"])
def create_project(
    payload: ProjectCreateRequest,
    project_service: ProjectService = Depends(get_project_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> ProjectDetailResponse:
    tenant_id = ctx.tenant_id if ctx else payload.tenant_id
    owner_id = ctx.user_id if ctx else payload.owner_id
    effective = ProjectCreateRequest(
        tenant_id=tenant_id,
        name=payload.name,
        description=payload.description,
        owner_id=owner_id,
        project_type=payload.project_type,
        matrix_config=payload.matrix_config,
        team_members=payload.team_members,
        agent_ids=payload.agent_ids,
        workflow_ids=payload.workflow_ids,
    )
    project = project_service.create_project(effective, actor_user_id=ctx.user_id if ctx else None)
    return _build_project_detail(project)


@router.get("/projects", response_model=ProjectListResponse, tags=["projects"])
def list_projects(
    tenant_id: UUID | None = Query(default=None),
    owner_id: UUID | None = Query(default=None),
    status_filter: ProjectStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, min_length=1, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    project_service: ProjectService = Depends(get_project_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> ProjectListResponse:
    effective_tenant = ctx.tenant_id if ctx else tenant_id
    items, total = project_service.list_projects(
        tenant_id=effective_tenant,
        owner_id=owner_id,
        status_filter=status_filter,
        search=search,
        limit=limit,
        offset=offset,
    )
    return ProjectListResponse(items=[_build_project_summary(p) for p in items], total=total)


@router.get("/projects/{project_id}", response_model=ProjectDetailResponse, tags=["projects"])
def get_project(
    project_id: UUID,
    project_service: ProjectService = Depends(get_project_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> ProjectDetailResponse:
    project = project_service.get_project(project_id)
    if ctx and project.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Project not found.")
    return _build_project_detail(project)


@router.put("/projects/{project_id}", response_model=ProjectDetailResponse, tags=["projects"])
def update_project(
    project_id: UUID,
    payload: ProjectUpdateRequest,
    project_service: ProjectService = Depends(get_project_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> ProjectDetailResponse:
    project = project_service.get_project(project_id)
    if ctx and project.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Project not found.")
    project = project_service.update_project(project_id, payload, actor_user_id=ctx.user_id if ctx else None)
    return _build_project_detail(project)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["projects"])
def delete_project(
    project_id: UUID,
    project_service: ProjectService = Depends(get_project_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> Response:
    project = project_service.get_project(project_id)
    if ctx and project.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Project not found.")
    project_service.delete_project(project_id, actor_user_id=ctx.user_id if ctx else None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
