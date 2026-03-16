"""WordPress 工具基类：解析 site_id、拼接 API、处理异常、返回标准 JSON。"""
from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel
from pydantic import Field

from tools.runtime.base import StructuredTool
from tools.runtime.base import ToolActionDefinition
from tools.runtime.base import ToolExecutionContext
from tools.runtime.base import ToolExecutionResult
from tools.runtime.base import ToolParameterDefinition
from tools.wordpress.site_resolver import resolve_site_credentials
from tools.wordpress.site_resolver import SiteCredentials


class SiteInputMixin(BaseModel):
    """所有 WordPress 工具的通用输入：site_id 必填。"""
    site_id: str = Field(..., description="WordPress 站点 ID (来自 WordPressSite 表)")


def _get_tenant_id(context: ToolExecutionContext) -> str | None:
    meta = context.metadata or {}
    tid = meta.get("tenant_id")
    return str(tid) if tid is not None else None


def _wp_request(
    creds: SiteCredentials,
    method: str,
    path: str,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> tuple[bool, dict[str, Any]]:
    """发起 WordPress REST API 请求，返回 (success, data)。"""
    url = f"{creds.api_url.rstrip('/')}{path}"
    auth = httpx.BasicAuth(creds.username, creds.app_password)

    try:
        with httpx.Client(auth=auth, timeout=30.0) as client:
            resp = client.request(method, url, json=json, params=params)
    except httpx.ConnectError as e:
        return False, {"error": f"连接失败: {e}"}
    except httpx.TimeoutException:
        return False, {"error": "请求超时"}

    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text, "status_code": resp.status_code}

    if resp.status_code >= 400:
        err = data.get("message", data.get("code", resp.text)) if isinstance(data, dict) else str(data)
        return False, {"error": err, "status_code": resp.status_code, "data": data}

    return True, data if isinstance(data, dict) else {"data": data}


def _tool_result(success: bool, output: dict[str, Any], context: ToolExecutionContext, action: str, name: str) -> ToolExecutionResult:
    return ToolExecutionResult(
        tool_name=name,
        action=action,
        success=success,
        output=output,
        error_message=output.get("error") if not success else None,
    )
