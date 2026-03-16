from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Response
from fastapi import status
from pydantic import BaseModel
from pydantic import Field

from app.core.config import get_settings
from app.core.dispatcher import dispatch_execution
from app.core.schemas import EngineWorkflowSnapshot
from app.core.schemas import ExecutionCreateRequest
from app.core.state import list_execution_summaries
from app.core.state import load_execution_state
from common.app.observability.health import build_health_status
from common.app.observability.prometheus import build_metrics_response
from common.app.observability.prometheus import format_metric

settings = get_settings()
router = APIRouter()


class ExecutionRequest(BaseModel):
    workflow_id: str
    workflow: EngineWorkflowSnapshot
    input_payload: dict[str, object] = Field(default_factory=dict)
    tenant_id: str | None = None
    task_run_id: str | None = None
    task_template_id: str | None = None


@router.get("/health/live", tags=["health"])
def live() -> dict:
    return build_health_status(settings.service_name, status="live").model_dump(mode="json")


@router.get("/health/ready", tags=["health"])
def ready() -> dict:
    return build_health_status(settings.service_name, status="ready").model_dump(mode="json")


@router.get("/metrics", tags=["observability"])
def metrics() -> Response:
    """Prometheus metrics: workflow executions total, success rate."""
    summaries = list_execution_summaries()
    completed = sum(1 for s in summaries if s.status == "completed")
    failed = sum(1 for s in summaries if s.status == "failed")
    running = sum(1 for s in summaries if s.status == "running")
    finalized = completed + failed
    success_rate = completed / finalized if finalized else 0.0
    payload = [
        format_metric(
            "ai_workforce_workflow_executions_total",
            "gauge",
            "Workflow executions by status.",
            [
                ({"status": "completed"}, completed),
                ({"status": "failed"}, failed),
                ({"status": "running"}, running),
            ],
        ),
        format_metric(
            "ai_workforce_workflow_success_rate",
            "gauge",
            "Ratio of completed workflow executions to finalized.",
            [({}, round(success_rate, 6))],
        ),
    ]
    return build_metrics_response("\n".join(payload) + "\n")


@router.get(f"{settings.api_v1_prefix}/executions", tags=["engine"])
def list_executions() -> dict:
    items = [item.model_dump(mode="json") for item in list_execution_summaries()]
    return {"items": items}


@router.get(f"{settings.api_v1_prefix}/executions/{{execution_id}}", tags=["engine"])
def get_execution(execution_id: str) -> dict:
    state = load_execution_state(execution_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow execution not found.",
        )
    return state.model_dump(mode="json")


@router.post(f"{settings.api_v1_prefix}/executions", tags=["engine"])
def create_execution(payload: ExecutionRequest) -> dict:
    if payload.tenant_id and settings.admin_service_url:
        from common.app.quota_client import check_quota
        allowed, err = check_quota(settings.admin_service_url, tenant_id=payload.tenant_id, resource="workflows_per_month")
        if not allowed:
            raise HTTPException(status_code=429, detail=err or "Workflow runs quota exceeded for this month.")
    exec_payload = ExecutionCreateRequest(
        workflow_id=payload.workflow_id,
        workflow=payload.workflow,
        input_payload=payload.input_payload,
        tenant_id=payload.tenant_id,
        task_run_id=payload.task_run_id,
    )
    execution = dispatch_execution(
        payload=exec_payload,
        broker_stream=settings.broker_stream,
    )
    return execution.model_dump(mode="json")
