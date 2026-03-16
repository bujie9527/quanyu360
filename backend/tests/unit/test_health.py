"""Unit tests for health/observability module."""
from __future__ import annotations

from common.app.observability.health import build_health_status
from common.app.schemas.health import HealthStatus


def test_build_health_status_returns_valid_schema() -> None:
    """build_health_status returns HealthStatus with expected fields."""
    result = build_health_status("test-service")

    assert isinstance(result, HealthStatus)
    assert result.service == "test-service"
    assert result.status == "ok"
    assert result.timestamp is not None


def test_build_health_status_custom_status() -> None:
    """build_health_status accepts custom status."""
    result = build_health_status("svc", status="degraded")

    assert result.status == "degraded"
