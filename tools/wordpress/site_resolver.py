"""解析 WordPressSite 凭证，供工具调用 WordPress REST API。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class SiteCredentials:
    api_url: str
    username: str
    app_password: str


def resolve_site_credentials(site_id: str, tenant_id: str | None) -> SiteCredentials:
    """
    从 project-service 获取 WordPress 站点凭证。
    site_id: WordPressSite UUID
    tenant_id: 租户 ID，从 context.metadata 获取
    """
    base_url = os.environ.get("PROJECT_SERVICE_URL", "http://project-service:8002").rstrip("/")
    url = f"{base_url}/sites/{site_id}/credentials"

    params: dict[str, Any] = {}
    if tenant_id:
        params["tenant_id"] = tenant_id

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, params=params or None)
    except httpx.ConnectError as e:
        raise RuntimeError(f"无法连接 project-service: {e}") from e
    except httpx.TimeoutException:
        raise RuntimeError("获取站点凭证超时") from None

    if resp.status_code == 404:
        raise ValueError("站点不存在或无权访问")
    if resp.status_code != 200:
        raise RuntimeError(f"获取凭证失败: HTTP {resp.status_code}")

    data = resp.json()
    api_url = data.get("api_url") or ""
    username = data.get("username") or ""
    app_password = data.get("app_password") or ""

    if not api_url or not username or not app_password:
        raise ValueError("站点凭证不完整")

    return SiteCredentials(api_url=api_url, username=username, app_password=app_password)
