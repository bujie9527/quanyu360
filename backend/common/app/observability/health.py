from __future__ import annotations

import os
from datetime import datetime, timezone

from common.app.schemas.health import HealthStatus


def build_health_status(service_name: str, status: str = "ok") -> HealthStatus:
    return HealthStatus(
        status=status,
        service=service_name,
        timestamp=datetime.now(timezone.utc),
    )


def check_db(url: str | None) -> bool:
    """Probe database connectivity."""
    if not url:
        return True
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.pool import NullPool
        engine = create_engine(url, pool_pre_ping=True, poolclass=NullPool)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def check_redis(url: str | None) -> bool:
    """Probe Redis connectivity."""
    if not url:
        return True
    try:
        import redis
        r = redis.from_url(url)
        r.ping()
        return True
    except Exception:
        return False


def check_ready(
    service_name: str,
    database_url: str | None = None,
    redis_url: str | None = None,
) -> HealthStatus:
    """Build ready status with dependency checks."""
    db_url = database_url or os.getenv("DATABASE_URL")
    rds_url = redis_url or os.getenv("REDIS_URL")
    ok = check_db(db_url) and check_redis(rds_url)
    return HealthStatus(
        status="ready" if ok else "degraded",
        service=service_name,
        timestamp=datetime.now(timezone.utc),
    )
