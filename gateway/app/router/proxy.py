"""Reverse proxy routing to internal services."""
from __future__ import annotations

from urllib.parse import urljoin

import httpx
from fastapi import Request
from fastapi import Response

from app.config import get_settings

# (path_prefix, config_attr, rewrite_backend_base)
# rewrite_backend_base: None = use path as-is; str = use as backend path prefix
ROUTE_MAP = [
    ("/api/v1/analytics", "agent_runtime_url", "/api/v1/analytics"),
    ("/api/v1/executions", "workflow_engine_url", "/api/v1/executions"),
    ("/api/v1/webhooks", "workflow_service_url", "/workflows/webhooks"),
    ("/api/executions", "workflow_engine_url", "/api/v1/executions"),
    ("/api/runtime", "agent_runtime_url", "/api/v1"),
    ("/api/auth", "auth_service_url", None),
    ("/api/projects", "project_service_url", None),
    ("/api/sites", "project_service_url", None),
    ("/api/agent", "agent_service_url", None),
    ("/api/agents", "agent_service_url", None),
    ("/api/tasks", "task_service_url", None),
    ("/api/workflows", "workflow_service_url", None),
    ("/api/task_templates", "workflow_service_url", None),
    ("/api/schedules", "workflow_service_url", None),
    ("/api/task_runs", "workflow_service_url", None),
    # tools 从 agent-runtime 获取（真实工具插件），tool-service 为 stub
    ("/api/tools", "agent_runtime_url", "/api/v1/tools"),
    ("/api/admin", "admin_service_url", None),
    ("/agents", "agent_service_url", None),
    ("/projects", "project_service_url", None),
    ("/sites", "project_service_url", None),
    ("/workflows", "workflow_service_url", None),
    ("/workflow", "workflow_service_url", None),
    ("/task_templates", "workflow_service_url", None),
    ("/schedules", "workflow_service_url", None),
    ("/task_runs", "workflow_service_url", None),
]


def _resolve_upstream(path: str) -> tuple[str, str] | None:
    """Return (base_url, backend_path) for the given request path."""
    settings = get_settings()
    for prefix, attr, rewrite_base in ROUTE_MAP:
        if path == prefix or path.startswith(prefix + "/"):
            base_url = getattr(settings, attr)
            if rewrite_base:
                suffix = path[len(prefix) :].lstrip("/")
                backend_path = f"{rewrite_base.rstrip('/')}/{suffix}" if suffix else rewrite_base.rstrip("/") or "/"
            else:
                backend_path = path[len("/api") :] if path.startswith("/api") else path
                backend_path = backend_path or "/"
            return base_url.rstrip("/"), backend_path
    return None


async def proxy_request(request: Request, path: str) -> Response:
    """Proxy request to the appropriate backend service."""
    resolved = _resolve_upstream(path)
    if not resolved:
        return Response(content='{"detail":"Not Found"}', status_code=404, media_type="application/json")
    base_url, backend_path = resolved
    url = urljoin(base_url + "/", backend_path.lstrip("/"))
    if request.url.query:
        url = f"{url}?{request.url.query}"

    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}
    body = await request.body()

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.request(method=request.method, url=url, headers=headers, content=body)
    return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))
