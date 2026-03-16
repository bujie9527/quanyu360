"""API Gateway - FastAPI service with JWT, rate limiting, logging, and routing."""
from __future__ import annotations

import logging

import httpx
import structlog
from fastapi import FastAPI
from fastapi import Request
from fastapi import Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.middleware.jwt import JWTAuthMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import limiter
from app.router.proxy import proxy_request

PROMETHEUS_CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)
logging.basicConfig(level=get_settings().log_level)

app = FastAPI(title="AI Workforce Platform - API Gateway", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(JWTAuthMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health/live", tags=["health"])
def live() -> dict:
    return {"status": "live", "service": "api-gateway"}


@app.get("/health/ready", tags=["health"])
def ready() -> dict:
    return {"status": "ready", "service": "api-gateway"}


async def _fetch_metrics(url: str) -> str:
    """Fetch Prometheus metrics from a service. Returns empty string on failure."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{url.rstrip('/')}/metrics")
            if resp.status_code == 200:
                return resp.text
    except Exception:
        pass
    return ""


async def _get_aggregated_metrics() -> str:
    """Fetch and merge Prometheus metrics from all metric sources."""
    settings = get_settings()
    task_text = await _fetch_metrics(settings.task_service_url)
    runtime_text = await _fetch_metrics(settings.agent_runtime_url)
    workflow_text = await _fetch_metrics(settings.workflow_engine_url)
    return "\n".join(filter(None, [task_text, runtime_text, workflow_text])) or "# No metrics available\n"


@app.get("/api/metrics", tags=["observability"])
@app.get("/api/v1/metrics", tags=["observability"])
@limiter.exempt
async def aggregated_metrics() -> Response:
    """
    Aggregated Prometheus metrics from task-service, agent-runtime, workflow-engine.
    Includes: tasks_executed, task_success_rate, agent_execution_time, token_usage, workflow metrics.
    """
    merged = await _get_aggregated_metrics()
    return Response(
        content=merged,
        media_type=PROMETHEUS_CONTENT_TYPE,
    )


@app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@limiter.limit(get_settings().rate_limit_default)
async def api_v1_proxy(request: Request, path: str):
    full_path = f"/api/v1/{path}" if path else "/api/v1"
    return await proxy_request(request, full_path)


@app.api_route("/api/projects", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@app.api_route("/api/projects/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@limiter.limit(get_settings().rate_limit_default)
async def api_projects_proxy(request: Request, path: str = ""):
    full_path = f"/api/projects/{path}" if path else "/api/projects"
    return await proxy_request(request, full_path)


@app.api_route("/api/sites", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@app.api_route("/api/sites/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@limiter.limit(get_settings().rate_limit_default)
async def api_sites_proxy(request: Request, path: str = ""):
    full_path = f"/api/sites/{path}" if path else "/api/sites"
    return await proxy_request(request, full_path)


@app.api_route("/api/tools", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@app.api_route("/api/tools/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@limiter.limit(get_settings().rate_limit_default)
async def api_tools_proxy(request: Request, path: str = ""):
    full_path = f"/api/tools/{path}" if path else "/api/tools"
    return await proxy_request(request, full_path)


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@limiter.limit(get_settings().rate_limit_default)
async def api_proxy(request: Request, path: str):
    full_path = f"/api/{path}" if path else "/api"
    return await proxy_request(request, full_path)


@app.api_route("/agents", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@app.api_route("/agents/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@limiter.limit(get_settings().rate_limit_default)
async def agents_proxy(request: Request, path: str = ""):
    full_path = f"/agents/{path}" if path else "/agents"
    return await proxy_request(request, full_path)


@app.api_route("/projects", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@app.api_route("/projects/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@limiter.limit(get_settings().rate_limit_default)
async def projects_proxy(request: Request, path: str = ""):
    full_path = f"/projects/{path}" if path else "/projects"
    return await proxy_request(request, full_path)


@app.api_route("/sites", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@app.api_route("/sites/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@limiter.limit(get_settings().rate_limit_default)
async def sites_proxy(request: Request, path: str = ""):
    full_path = f"/sites/{path}" if path else "/sites"
    return await proxy_request(request, full_path)


@app.api_route("/workflows", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@app.api_route("/workflows/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@limiter.limit(get_settings().rate_limit_default)
async def workflows_proxy(request: Request, path: str = ""):
    full_path = f"/workflows/{path}" if path else "/workflows"
    return await proxy_request(request, full_path)


@app.api_route("/workflow", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@app.api_route("/workflow/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@limiter.limit(get_settings().rate_limit_default)
async def workflow_proxy(request: Request, path: str = ""):
    full_path = f"/workflow/{path}" if path else "/workflow"
    return await proxy_request(request, full_path)


@app.api_route("/task_templates", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@app.api_route("/task_templates/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@limiter.limit(get_settings().rate_limit_default)
async def task_templates_proxy(request: Request, path: str = ""):
    full_path = f"/task_templates/{path}" if path else "/task_templates"
    return await proxy_request(request, full_path)


@app.api_route("/schedules", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@app.api_route("/schedules/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@limiter.limit(get_settings().rate_limit_default)
async def schedules_proxy(request: Request, path: str = ""):
    full_path = f"/schedules/{path}" if path else "/schedules"
    return await proxy_request(request, full_path)
