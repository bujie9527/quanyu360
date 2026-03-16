"""Health endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health/live", tags=["health"])
def live() -> dict:
    return {"status": "live", "service": "tool-service"}


@router.get("/health/ready", tags=["health"])
def ready() -> dict:
    return {"status": "ready", "service": "tool-service"}
