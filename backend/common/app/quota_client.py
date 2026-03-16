"""Quota check client. Calls admin-service to verify tenant has quota before execution."""
from __future__ import annotations

import httpx


def check_quota(
    base_url: str | None,
    *,
    tenant_id: str,
    resource: str,
) -> tuple[bool, str | None]:
    """
    Check if tenant has quota for resource.
    Returns (allowed, error_message).
    resource: tasks_per_month | llm_requests_per_month | workflows_per_month | wordpress_sites_per_month
    """
    if not base_url or not tenant_id:
        return True, None
    if resource not in ("tasks_per_month", "llm_requests_per_month", "workflows_per_month", "wordpress_sites_per_month"):
        return True, None
    try:
        url = f"{base_url.rstrip('/')}/admin/quotas/check"
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url, params={"tenant_id": tenant_id, "resource": resource})
            if resp.status_code >= 400:
                return False, f"Quota check failed: {resp.status_code}"
            data = resp.json()
            allowed = data.get("allowed", True)
            if not allowed:
                msg = data.get("message", f"Quota exceeded for {resource}")
                return False, msg
            return True, None
    except Exception:
        return True, None


def check_quota_with_count(
    base_url: str | None,
    *,
    tenant_id: str,
    resource: str,
    requested_count: int,
) -> tuple[bool, str | None]:
    """
    Check if tenant has quota for resource when adding requested_count.
    Returns (allowed, error_message).
    """
    if not base_url or not tenant_id or requested_count <= 0:
        return True, None
    if resource not in ("tasks_per_month", "llm_requests_per_month", "workflows_per_month", "wordpress_sites_per_month"):
        return True, None
    try:
        url = f"{base_url.rstrip('/')}/admin/quotas/check"
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url, params={"tenant_id": tenant_id, "resource": resource})
            if resp.status_code >= 400:
                return False, f"Quota check failed: {resp.status_code}"
            data = resp.json()
            current = data.get("current", 0)
            limit = data.get("limit", 0)
            if limit <= 0:
                return True, None
            if current + requested_count > limit:
                return False, f"Quota exceeded for {resource}: would be {current + requested_count}/{limit}"
            return True, None
    except Exception:
        return True, None
