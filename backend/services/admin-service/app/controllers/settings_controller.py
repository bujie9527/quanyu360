"""Admin system configuration HTTP endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from app.dependencies import get_db_session
from app.repositories.system_config_repository import SystemConfigRepository
from app.schemas.system_config_schemas import SystemConfigBulkUpdateRequest
from app.schemas.system_config_schemas import SystemConfigItemResponse
from app.schemas.system_config_schemas import SystemConfigUpdateRequest
from app.services.system_config_service import SystemConfigService
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin", tags=["settings"])


def _get_config_service(db: Session = Depends(get_db_session)) -> SystemConfigService:
    repo = SystemConfigRepository(db)
    return SystemConfigService(repo)


@router.get("/settings", response_model=list[SystemConfigItemResponse])
def list_system_settings(
    category: str | None = Query(default=None, max_length=60),
    service: SystemConfigService = Depends(_get_config_service),
) -> list[SystemConfigItemResponse]:
    """List all system config entries. Secrets are masked."""
    items = service.list_configs(category=category)
    return [SystemConfigItemResponse(**x) for x in items]


@router.get("/settings/{key}", response_model=SystemConfigItemResponse)
def get_system_setting(
    key: str,
    service: SystemConfigService = Depends(_get_config_service),
) -> SystemConfigItemResponse:
    """Get one config by key. Secret value is masked."""
    return SystemConfigItemResponse(**service.get_config(key))


@router.put("/settings/{key}", response_model=SystemConfigItemResponse)
def update_system_setting(
    key: str,
    payload: SystemConfigUpdateRequest,
    service: SystemConfigService = Depends(_get_config_service),
) -> SystemConfigItemResponse:
    """Update a config entry. For secrets, pass new value; leave empty to keep existing."""
    try:
        existing = service.get_config(key)
    except HTTPException:
        existing = None
    cat = payload.category if payload.category is not None else (existing["category"] if existing else "general")
    is_sec = payload.is_secret if payload.is_secret is not None else (existing["is_secret"] if existing else False)
    desc = payload.description if payload.description is not None else (existing["description"] if existing else None)
    if is_sec and not payload.value and existing and existing.get("value_set"):
        return SystemConfigItemResponse(**existing)
    result = service.set_config(
        key=key,
        value=payload.value,
        category=cat,
        is_secret=is_sec,
        description=desc,
    )
    return SystemConfigItemResponse(**result)


@router.post("/settings/bulk", response_model=list[SystemConfigItemResponse])
def bulk_update_settings(
    payload: SystemConfigBulkUpdateRequest,
    service: SystemConfigService = Depends(_get_config_service),
) -> list[SystemConfigItemResponse]:
    """Create or update multiple config entries."""
    results = []
    for item in payload.items:
        r = service.set_config(
            key=item.key,
            value=item.value,
            category=item.category,
            is_secret=item.is_secret,
            description=item.description,
        )
        results.append(SystemConfigItemResponse(**r))
    return results
