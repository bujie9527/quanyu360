"""QuotaService: check tenant quotas and block execution when exceeded."""
from __future__ import annotations

from datetime import datetime
from datetime import timezone
from datetime import timedelta
from uuid import UUID

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from common.app.models import Project
from common.app.models import Task
from common.app.models import Tenant
from common.app.models import UsageLog
from common.app.models import UsageType
from common.app.models import WordPressSite

DEFAULT_TASKS_PER_MONTH = 1000
DEFAULT_LLM_REQUESTS_PER_MONTH = 5000
DEFAULT_WORKFLOWS_PER_MONTH = 100
DEFAULT_WORDPRESS_SITES_PER_MONTH = 10


def _month_range() -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1) - timedelta(microseconds=1)
    else:
        end = start.replace(month=start.month + 1) - timedelta(microseconds=1)
    return start, end


def _get_quota_limits(tenant: Tenant) -> dict[str, int]:
    quotas = (tenant.settings or {}).get("quotas") or {}
    return {
        "tasks_per_month": int(quotas.get("tasks_per_month", DEFAULT_TASKS_PER_MONTH)),
        "llm_requests_per_month": int(quotas.get("llm_requests_per_month", DEFAULT_LLM_REQUESTS_PER_MONTH)),
        "workflows_per_month": int(quotas.get("workflows_per_month", DEFAULT_WORKFLOWS_PER_MONTH)),
        "wordpress_sites_per_month": int(quotas.get("wordpress_sites_per_month", DEFAULT_WORDPRESS_SITES_PER_MONTH)),
    }


class QuotaCheckResult:
    def __init__(
        self,
        allowed: bool,
        current: int,
        limit: int,
        resource: str,
        tenant_id: UUID,
        message: str | None = None,
    ) -> None:
        self.allowed = allowed
        self.current = current
        self.limit = limit
        self.resource = resource
        self.tenant_id = tenant_id
        self.message = message or (f"Quota exceeded: {resource} ({current}/{limit})" if not allowed else None)


class QuotaService:
    """Check tenant quotas. Block execution when exceeded."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def check(
        self,
        tenant_id: str | UUID,
        resource: str,
    ) -> QuotaCheckResult:
        """
        Check if tenant has quota for resource.
        resource: tasks_per_month | llm_requests_per_month | workflows_per_month
        """
        tid = UUID(str(tenant_id)) if isinstance(tenant_id, str) else tenant_id
        tenant = self.db.get(Tenant, tid)
        if not tenant:
            return QuotaCheckResult(allowed=False, current=0, limit=0, resource=resource, tenant_id=tid, message="Tenant not found")

        limits = _get_quota_limits(tenant)
        limit = limits.get(resource)
        if limit is None:
            return QuotaCheckResult(allowed=True, current=0, limit=0, resource=resource, tenant_id=tid)

        start, end = _month_range()

        if resource == "tasks_per_month":
            stmt = select(func.count(Task.id)).where(
                Task.project_id.in_(select(Project.id).where(Project.tenant_id == tid)),
                Task.created_at >= start,
                Task.created_at <= end,
            )
            current = self.db.scalar(stmt) or 0
        elif resource == "llm_requests_per_month":
            stmt = select(func.count(UsageLog.id)).where(
                UsageLog.tenant_id == tid,
                UsageLog.usage_type == UsageType.llm_tokens,
                UsageLog.created_at >= start,
                UsageLog.created_at <= end,
            )
            current = self.db.scalar(stmt) or 0
        elif resource == "workflows_per_month":
            stmt = select(func.coalesce(func.sum(UsageLog.quantity), 0)).where(
                UsageLog.tenant_id == tid,
                UsageLog.usage_type == UsageType.workflow_run,
                UsageLog.created_at >= start,
                UsageLog.created_at <= end,
            )
            current = int(self.db.scalar(stmt) or 0)
        elif resource == "wordpress_sites_per_month":
            stmt = select(func.count(WordPressSite.id)).where(
                WordPressSite.tenant_id == tid,
                WordPressSite.created_at >= start,
                WordPressSite.created_at <= end,
            )
            current = self.db.scalar(stmt) or 0
        else:
            return QuotaCheckResult(allowed=True, current=0, limit=limit, resource=resource, tenant_id=tid)

        allowed = current < limit
        return QuotaCheckResult(
            allowed=allowed,
            current=current,
            limit=limit,
            resource=resource,
            tenant_id=tid,
        )

    def list_quotas(self, tenant_id: str | UUID) -> dict:
        """Return all quota resources (current, limit, allowed) for a tenant."""
        tid = UUID(str(tenant_id)) if isinstance(tenant_id, str) else tenant_id
        results = {}
        for res in ("tasks_per_month", "llm_requests_per_month", "workflows_per_month", "wordpress_sites_per_month"):
            r = self.check(tid, res)
            results[res] = {
                "current": r.current,
                "limit": r.limit,
                "allowed": r.allowed,
            }
        return {"tenant_id": tid, "quotas": results}

    def update_quotas(self, tenant_id: str | UUID, quotas: dict[str, int]) -> None:
        """Update tenant.settings.quotas. Merges with existing."""
        tid = UUID(str(tenant_id)) if isinstance(tenant_id, str) else tenant_id
        tenant = self.db.get(Tenant, tid)
        if not tenant:
            raise ValueError("Tenant not found")
        settings = dict(tenant.settings or {})
        existing = settings.get("quotas") or {}
        updated = {**existing}
        for k in ("tasks_per_month", "llm_requests_per_month", "workflows_per_month", "wordpress_sites_per_month"):
            if k in quotas and isinstance(quotas[k], int) and quotas[k] >= 0:
                updated[k] = quotas[k]
        settings["quotas"] = updated
        tenant.settings = settings
        self.db.commit()
