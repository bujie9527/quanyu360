"""Health and metrics endpoints."""
from fastapi import APIRouter, Response

from app.config import settings
from common.app.observability.health import build_health_status
from common.app.observability.prometheus import basic_service_metrics
from common.app.observability.prometheus import build_metrics_response

router = APIRouter()


@router.get("/metrics", tags=["observability"])
def metrics() -> Response:
    return build_metrics_response(basic_service_metrics(settings.service_name))


@router.get("/health/live", tags=["health"])
def live() -> dict:
    return build_health_status(settings.service_name, status="live").model_dump(mode="json")


@router.get("/health/ready", tags=["health"])
def ready() -> dict:
    return build_health_status(settings.service_name, status="ready").model_dump(mode="json")
