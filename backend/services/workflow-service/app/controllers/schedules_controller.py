"""Schedule HTTP endpoints."""
from __future__ import annotations

from datetime import datetime
from datetime import timezone
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status

from app.dependencies import get_schedule_service
from app.schemas import ScheduleCreateRequest
from app.schemas import ScheduleListResponse
from app.schemas import ScheduleResponse
from app.schemas import ScheduleUpdateRequest
from app.services import ScheduleService


router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: ScheduleCreateRequest,
    service: ScheduleService = Depends(get_schedule_service),
) -> ScheduleResponse:
    s = service.create(payload)
    return ScheduleResponse.model_validate(s)


@router.get("", response_model=ScheduleListResponse)
def list_schedules(
    task_template_id: UUID | None = Query(default=None),
    enabled: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: ScheduleService = Depends(get_schedule_service),
) -> ScheduleListResponse:
    items, total = service.list(
        task_template_id=task_template_id,
        enabled=enabled,
        limit=limit,
        offset=offset,
    )
    return ScheduleListResponse(items=[ScheduleResponse.model_validate(x) for x in items], total=total)


@router.get("/presets")
def get_cron_presets() -> dict[str, str]:
    """返回 hourly / daily / weekly 的 cron 预设。"""
    from app.schemas.schedule_schemas import CRON_PRESETS
    return CRON_PRESETS


@router.get("/due")
def list_due_schedules(
    at: str | None = Query(default=None, description="ISO8601 time, default now"),
    service: ScheduleService = Depends(get_schedule_service),
) -> dict:
    """列出指定时刻 due 的 schedules（供 scheduler 调用）。"""
    from datetime import datetime
    if at:
        try:
            now = datetime.fromisoformat(at.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            now = datetime.now(timezone.utc)
    else:
        now = datetime.now(timezone.utc)
    due = service.schedule_repo.list_due(now)
    return {"items": [{"id": str(s.id), "cron": s.cron} for s in due]}


@router.post("/tick", tags=["scheduler"])
def tick_schedules(
    service: ScheduleService = Depends(get_schedule_service),
) -> dict:
    """检查 due 的 schedules 并执行。由 APScheduler 每分钟调用。"""
    results = service.tick()
    return {"triggered": len(results), "results": results}


@router.post("/{schedule_id}/trigger")
def trigger_schedule(
    schedule_id: UUID,
    service: ScheduleService = Depends(get_schedule_service),
) -> dict:
    """手动触发指定 schedule。"""
    results = service.trigger(schedule_id)
    return {"results": results}


@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(
    schedule_id: UUID,
    service: ScheduleService = Depends(get_schedule_service),
) -> ScheduleResponse:
    s = service.get(schedule_id)
    return ScheduleResponse.model_validate(s)


@router.patch("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: UUID,
    payload: ScheduleUpdateRequest,
    service: ScheduleService = Depends(get_schedule_service),
) -> ScheduleResponse:
    s = service.update(schedule_id, payload)
    return ScheduleResponse.model_validate(s)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: UUID,
    service: ScheduleService = Depends(get_schedule_service),
) -> None:
    service.delete(schedule_id)
