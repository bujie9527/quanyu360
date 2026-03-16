"""Health endpoints."""
from fastapi import APIRouter

from app.config import settings
from common.app.observability.health import build_health_status

router = APIRouter()


@router.get("/health/live", tags=["health"])
def live() -> dict:
    return build_health_status(settings.service_name, status="live").model_dump(mode="json")


@router.get("/health/ready", tags=["health"])
def ready() -> dict:
    return build_health_status(settings.service_name, status="ready").model_dump(mode="json")
