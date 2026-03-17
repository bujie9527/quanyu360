"""Admin site pool and batch WordPress install endpoints."""
from __future__ import annotations

import re
import uuid
from uuid import UUID

import httpx
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status
from sqlalchemy import Select
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies import get_db_session
from app.schemas.site_pool_schemas import SitePoolAssignRequest
from app.schemas.site_pool_schemas import SitePoolBatchInstallRequest
from app.schemas.site_pool_schemas import SitePoolBatchInstallResponse
from app.schemas.site_pool_schemas import SitePoolInstallRunResponse
from app.schemas.site_pool_schemas import SitePoolInstallWorkflowListResponse
from app.schemas.site_pool_schemas import SitePoolInstallWorkflowResponse
from app.schemas.site_pool_schemas import SitePoolSiteListResponse
from app.schemas.site_pool_schemas import SitePoolSiteResponse
from app.schemas.site_pool_schemas import SitePoolStepLogResponse
from common.app.models import PlatformDomain
from common.app.models import PlatformDomainStatus
from common.app.models import Project
from common.app.models import Server
from common.app.models import ServerStatus
from common.app.models import StepRun
from common.app.models import TaskRun
from common.app.models import Tenant
from common.app.models import Workflow
from common.app.models import WordPressSite
from common.app.models import WordPressSiteStatus

router = APIRouter(prefix="/admin/site-pool", tags=["site-pool"])


def _infer_pool_status(site: WordPressSite, task_run: TaskRun | None) -> str:
    if site.status == WordPressSiteStatus.error:
        return "error"
    if site.tenant_id and site.project_id:
        return "assigned"
    if task_run and task_run.status in {"queued", "pending", "running"}:
        return "installing"
    if site.status == WordPressSiteStatus.inactive:
        return "installing"
    return "ready"


def _to_site_response(site: WordPressSite, task_run: TaskRun | None = None) -> SitePoolSiteResponse:
    return SitePoolSiteResponse(
        id=site.id,
        domain=site.domain,
        name=site.name,
        api_url=site.api_url,
        status=site.status.value,
        pool_status=_infer_pool_status(site, task_run),
        platform_domain_id=site.platform_domain_id,
        server_id=site.server_id,
        install_task_run_id=site.install_task_run_id,
        tenant_id=site.tenant_id,
        project_id=site.project_id,
        created_at=site.created_at,
        updated_at=site.updated_at,
    )


def _build_site_query(server_id: UUID | None, assigned: bool | None, status_filter: str | None) -> Select[tuple[WordPressSite]]:
    stmt = select(WordPressSite)
    if server_id is not None:
        stmt = stmt.where(WordPressSite.server_id == server_id)
    if assigned is True:
        stmt = stmt.where(WordPressSite.tenant_id.is_not(None), WordPressSite.project_id.is_not(None))
    elif assigned is False:
        stmt = stmt.where(WordPressSite.tenant_id.is_(None), WordPressSite.project_id.is_(None))
    if status_filter:
        stmt = stmt.where(WordPressSite.status == WordPressSiteStatus(status_filter))
    return stmt


@router.get("/sites", response_model=SitePoolSiteListResponse)
def list_site_pool(
    server_id: UUID | None = Query(default=None),
    assigned: bool | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status", pattern="^(active|inactive|error)$"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> SitePoolSiteListResponse:
    stmt = _build_site_query(server_id=server_id, assigned=assigned, status_filter=status_filter)
    rows = list(db.scalars(stmt.order_by(WordPressSite.created_at.desc()).offset(offset).limit(limit)).all())
    task_run_ids = [r.install_task_run_id for r in rows if r.install_task_run_id]
    task_run_map: dict[UUID, TaskRun] = {}
    if task_run_ids:
        task_runs = list(db.scalars(select(TaskRun).where(TaskRun.id.in_(task_run_ids))).all())
        task_run_map = {tr.id: tr for tr in task_runs}

    count_stmt = select(func.count(WordPressSite.id))
    if server_id is not None:
        count_stmt = count_stmt.where(WordPressSite.server_id == server_id)
    if assigned is True:
        count_stmt = count_stmt.where(WordPressSite.tenant_id.is_not(None), WordPressSite.project_id.is_not(None))
    elif assigned is False:
        count_stmt = count_stmt.where(WordPressSite.tenant_id.is_(None), WordPressSite.project_id.is_(None))
    if status_filter:
        count_stmt = count_stmt.where(WordPressSite.status == WordPressSiteStatus(status_filter))

    total = db.scalar(count_stmt) or 0
    return SitePoolSiteListResponse(
        items=[_to_site_response(r, task_run_map.get(r.install_task_run_id)) for r in rows],
        total=total,
    )


@router.get("/install-workflows", response_model=SitePoolInstallWorkflowListResponse)
def list_install_workflows(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> SitePoolInstallWorkflowListResponse:
    stmt = (
        select(Workflow)
        .where(Workflow.slug == "wp_site_install_workflow")
        .order_by(Workflow.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = list(db.scalars(stmt).all())
    total = db.scalar(select(func.count(Workflow.id)).where(Workflow.slug == "wp_site_install_workflow")) or 0
    return SitePoolInstallWorkflowListResponse(
        items=[
            SitePoolInstallWorkflowResponse(
                id=item.id,
                project_id=item.project_id,
                name=item.name,
                slug=item.slug,
                status=item.status.value,
            )
            for item in items
        ],
        total=total,
    )


@router.post("/batch-install", response_model=SitePoolBatchInstallResponse, status_code=status.HTTP_201_CREATED)
def batch_install(
    payload: SitePoolBatchInstallRequest,
    db: Session = Depends(get_db_session),
) -> SitePoolBatchInstallResponse:
    server = db.get(Server, payload.server_id)
    if server is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    if server.status != ServerStatus.active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Server is not active")

    workflow: Workflow | None = None
    if payload.workflow_id:
        workflow = db.get(Workflow, payload.workflow_id)
        if workflow is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    else:
        workflow = db.scalar(
            select(Workflow).where(Workflow.slug == "wp_site_install_workflow").order_by(Workflow.created_at.desc())
        )
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No install workflow available")

    domains = list(
        db.scalars(
            select(PlatformDomain).where(PlatformDomain.id.in_(payload.domain_ids)).order_by(PlatformDomain.created_at.asc())
        ).all()
    )
    if len(domains) != len(payload.domain_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Some domains were not found")

    for domain in domains:
        if domain.status != PlatformDomainStatus.available:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Domain not available: {domain.domain}")
        if domain.server_id and domain.server_id != server.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Domain {domain.domain} is bound to another server",
            )

    site_ids: list[UUID] = []
    task_run_ids: list[UUID] = []
    execution_items: list[tuple[UUID, UUID, PlatformDomain]] = []

    for index, domain in enumerate(domains, start=1):
        tr = TaskRun(
            workflow_id=workflow.id,
            execution_id=str(uuid.uuid4()),
            task_template_id=None,
            status="running",
        )
        db.add(tr)
        db.flush()

        site = WordPressSite(
            platform_domain_id=domain.id,
            server_id=server.id,
            install_task_run_id=tr.id,
            tenant_id=None,
            project_id=None,
            name=f"{payload.site_title_prefix} #{index}",
            domain=domain.domain,
            api_url=domain.api_base_url.rstrip("/"),
            username=payload.admin_username,
            app_password=payload.admin_password,
            status=WordPressSiteStatus.inactive,
        )
        db.add(site)
        db.flush()

        if domain.server_id is None:
            domain.server_id = server.id
        domain.status = PlatformDomainStatus.assigned

        site_ids.append(site.id)
        task_run_ids.append(tr.id)
        execution_items.append((tr.id, site.id, domain))

    db.commit()

    _trigger_batch_install_workflows(
        workflow_service_url=settings.workflow_service_url,
        workflow_id=workflow.id,
        execution_items=execution_items,
        server=server,
        payload=payload,
    )

    return SitePoolBatchInstallResponse(site_ids=site_ids, task_run_ids=task_run_ids)


def _trigger_batch_install_workflows(
    *,
    workflow_service_url: str,
    workflow_id: UUID,
    execution_items: list[tuple[UUID, UUID, PlatformDomain]],
    server: Server,
    payload: SitePoolBatchInstallRequest,
) -> None:
    base = workflow_service_url.rstrip("/")
    for task_run_id, site_id, domain in execution_items:
        db_name = f"{server.mysql_db_prefix}{re.sub(r'[^a-zA-Z0-9_]', '_', domain.domain)}".lower()[:64]
        wp_path = f"{server.web_root.rstrip('/')}/{domain.domain}"
        input_payload = {
            "domain": domain.domain,
            "wordpress_site_id": str(site_id),
            "site_name": domain.domain,
            "url": f"http://{domain.domain}",
            "title": f"{payload.site_title_prefix} - {domain.domain}",
            "path": wp_path,
            "db_name": db_name,
            "db_user": server.mysql_admin_user,
            "db_password": server.mysql_admin_password,
            "db_host": server.mysql_host,
            "mysql_admin_user": server.mysql_admin_user,
            "mysql_admin_password": server.mysql_admin_password,
            "admin_user": payload.admin_username,
            "admin_password": payload.admin_password,
            "admin_email": payload.admin_email,
            "wp_user": payload.admin_username,
            "host": server.host,
            "port": server.port,
            "ssh_user": server.ssh_user,
            "ssh_password": server.ssh_password,
            "ssh_private_key": server.ssh_private_key,
            "wp_cli_bin": server.wp_cli_bin,
            "project_service_url": "http://project-service:8002",
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    f"{base}/workflows/{workflow_id}/execute",
                    json={"task_run_id": str(task_run_id), "input_payload": input_payload},
                )
                resp.raise_for_status()
        except Exception:
            # 仅记录失败，站点状态将通过后续运维处理。
            continue


@router.patch("/sites/{site_id}/assign", response_model=SitePoolSiteResponse)
def assign_site_to_tenant(
    site_id: UUID,
    payload: SitePoolAssignRequest,
    db: Session = Depends(get_db_session),
) -> SitePoolSiteResponse:
    site = db.get(WordPressSite, site_id)
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    tenant = db.get(Tenant, payload.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    project = db.get(Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.tenant_id != tenant.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project does not belong to tenant")

    site.tenant_id = tenant.id
    site.project_id = project.id
    if site.status == WordPressSiteStatus.inactive:
        site.status = WordPressSiteStatus.active
    db.commit()
    db.refresh(site)

    task_run = db.get(TaskRun, site.install_task_run_id) if site.install_task_run_id else None
    return _to_site_response(site, task_run)


@router.get("/sites/{site_id}/install-run", response_model=SitePoolInstallRunResponse | None)
def get_site_install_run(site_id: UUID, db: Session = Depends(get_db_session)) -> SitePoolInstallRunResponse | None:
    site = db.get(WordPressSite, site_id)
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    if site.install_task_run_id is None:
        return None

    task_run = db.get(TaskRun, site.install_task_run_id)
    if task_run is None:
        return None

    steps = list(
        db.scalars(select(StepRun).where(StepRun.task_run_id == task_run.id).order_by(StepRun.created_at.asc())).all()
    )
    return SitePoolInstallRunResponse(
        task_run_id=task_run.id,
        status=task_run.status,
        start_time=task_run.start_time,
        end_time=task_run.end_time,
        steps=[
            SitePoolStepLogResponse(
                id=s.id,
                step_name=s.step_name,
                status=s.status,
                duration=s.duration,
                output_json=s.output_json or {},
                created_at=s.created_at,
            )
            for s in steps
        ],
    )

