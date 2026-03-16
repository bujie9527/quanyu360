"""Unit tests for Pydantic schemas."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from common.app.schemas.health import HealthStatus


def test_health_status_schema() -> None:
    """HealthStatus validates required fields."""
    hs = HealthStatus(
        status="ok",
        service="auth-service",
        timestamp=datetime.now(timezone.utc),
    )
    assert hs.status == "ok"
    assert hs.service == "auth-service"


def test_health_status_serialization() -> None:
    """HealthStatus can be serialized to dict."""
    hs = HealthStatus(
        status="ok",
        service="svc",
        timestamp=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )
    d = hs.model_dump()
    assert d["status"] == "ok"
    assert d["service"] == "svc"
    assert "timestamp" in d
