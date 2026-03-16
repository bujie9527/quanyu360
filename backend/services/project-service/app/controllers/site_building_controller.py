"""Site building batch HTTP endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from app.config import settings
from app.dependencies import get_db_session
from app.dependencies import get_tenant_context_dep
from app.schemas.site_building_schemas import SiteBuildingBatchRequest
from app.schemas.site_building_schemas import SiteBuildingBatchResponse
from app.services.site_building_service import SiteBuildingResult
from app.services.site_building_service import SiteBuildingService
from common.app.auth import TenantContext
from sqlalchemy.orm import Session

router = APIRouter(prefix="/projects", tags=["site-building"])


def _get_service(db: Session = Depends(get_db_session)) -> SiteBuildingService:
    return SiteBuildingService(
        db,
        admin_service_url=settings.admin_service_url,
        workflow_service_url=settings.workflow_service_url,
    )


@router.post("/site_building/batch", response_model=SiteBuildingBatchResponse, status_code=status.HTTP_201_CREATED)
def create_site_building_batch(
    payload: SiteBuildingBatchRequest,
    service: SiteBuildingService = Depends(_get_service),
    ctx: TenantContext | None = Depends(get_tenant_context_dep),
) -> SiteBuildingBatchResponse:
    """Create batch WordPress site placeholders. Requires tenant auth."""
    if not ctx:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录")
    try:
        result: SiteBuildingResult = service.create_batch(
            tenant_id=ctx.tenant_id,
            project_id=payload.project_id,
            count=payload.count,
            domain_ids=payload.domain_ids,
            workflow_id=payload.workflow_id,
        )
        service.db.commit()
        service.trigger_workflows_for_site_building(result)
        return SiteBuildingBatchResponse(
            wordpress_site_ids=result.wordpress_site_ids,
            task_run_ids=result.task_run_ids,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
