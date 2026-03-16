"""Workflow HTTP endpoints."""
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Request
from fastapi import Response
from fastapi import status

from app.dependencies import get_workflow_service
from app.schemas import WorkflowBuilderCreateRequest
from app.schemas import WorkflowBuilderDetailResponse
from app.schemas import WorkflowCreateRequest
from app.schemas import WorkflowDetailResponse
from app.schemas import WorkflowExecutionRequest
from app.schemas import WorkflowExecutionResponse
from app.schemas import WorkflowEventTriggerRequest
from app.schemas import WorkflowListResponse
from app.schemas import WorkflowRunRequest
from app.schemas import WorkflowConfigurationResponse
from app.schemas import WorkflowEdgeResponse
from app.schemas import WorkflowNodeResponse
from app.schemas import WorkflowStepResponse
from app.schemas import WorkflowSummaryResponse
from app.schemas import WorkflowUpdateRequest
from app.services import WorkflowService
from common.app.models import Workflow
from common.app.models import WorkflowStatus
from common.app.models import WorkflowTriggerType

router = APIRouter()


def _build_workflow_summary(workflow: Workflow) -> WorkflowSummaryResponse:
    return WorkflowSummaryResponse(
        id=workflow.id,
        project_id=workflow.project_id,
        name=workflow.name,
        slug=workflow.slug,
        version=workflow.version,
        status=workflow.status.value,
        trigger_type=workflow.trigger_type.value,
        step_count=len(workflow.steps),
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )


def _build_workflow_builder_detail(workflow: Workflow) -> WorkflowBuilderDetailResponse:
    """Build builder-format response from workflow (definition or steps)."""
    definition = workflow.definition or {}
    nodes_data = definition.get("nodes")
    edges_data = definition.get("edges")
    config_data = definition.get("configuration") or {}
    if not nodes_data and workflow.steps:
        nodes_data = [
            {
                "id": step.step_key,
                "type": {"agent_task": "agent_node", "tool_call": "tool_node", "condition": "condition_node", "delay": "delay_node"}.get(step.step_type.value, "agent_node"),
                "data": {"name": step.name, **step.config, "assigned_agent_id": str(step.assigned_agent_id) if step.assigned_agent_id else None, "tool_id": str(step.tool_id) if step.tool_id else None},
            }
            for step in sorted(workflow.steps, key=lambda s: s.sequence)
        ]
        edges_data = [
            {"source": s.step_key, "target": s.next_step_key}
            for s in workflow.steps
            if s.next_step_key
        ]
    def _to_node(n: dict) -> WorkflowNodeResponse:
        data = n.get("data")
        if not isinstance(data, dict):
            data = {k: v for k, v in n.items() if k not in ("id", "type", "position")}
        return WorkflowNodeResponse(id=str(n.get("id", "")), type=str(n.get("type", "agent_node")), data=data or {}, position=n.get("position"))

    nodes = [_to_node(n) for n in (nodes_data or [])]
    edges = [WorkflowEdgeResponse(id=e.get("id"), source=e.get("source", ""), target=e.get("target", ""), sourceHandle=e.get("sourceHandle") or e.get("source_handle"), targetHandle=e.get("targetHandle") or e.get("target_handle")) for e in (edges_data or [])]
    config = WorkflowConfigurationResponse(
        trigger_type=config_data.get("trigger_type", workflow.trigger_type.value),
        trigger_config=config_data.get("trigger_config"),
        entry_node_id=config_data.get("entry_node_id"),
        metadata=config_data.get("metadata", {}),
    )
    return WorkflowBuilderDetailResponse(
        id=workflow.id,
        project_id=workflow.project_id,
        name=workflow.name,
        slug=workflow.slug,
        version=workflow.version,
        status=workflow.status.value,
        nodes=nodes,
        edges=edges,
        configuration=config,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )


def _build_workflow_detail(workflow: Workflow) -> WorkflowDetailResponse:
    return WorkflowDetailResponse(
        id=workflow.id,
        project_id=workflow.project_id,
        name=workflow.name,
        slug=workflow.slug,
        version=workflow.version,
        status=workflow.status.value,
        trigger_type=workflow.trigger_type.value,
        definition=workflow.definition,
        steps=[
            WorkflowStepResponse(
                id=step.id,
                workflow_id=step.workflow_id,
                step_key=step.step_key,
                name=step.name,
                type=step.step_type.value,
                config=step.config,
                next_step=step.next_step_key,
                sequence=step.sequence,
                retry_limit=step.retry_limit,
                timeout_seconds=step.timeout_seconds,
                assigned_agent_id=step.assigned_agent_id,
                tool_id=step.tool_id,
            )
            for step in sorted(workflow.steps, key=lambda s: s.sequence)
        ],
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
        published_at=workflow.published_at,
    )


@router.post("/workflows", response_model=WorkflowDetailResponse, status_code=status.HTTP_201_CREATED, tags=["workflows"])
def create_workflow(
    payload: WorkflowCreateRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowDetailResponse:
    workflow = workflow_service.create_workflow(payload)
    return _build_workflow_detail(workflow)


@router.get("/workflows/scheduled", tags=["workflows", "triggers"])
def list_scheduled_workflows(
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    """List active scheduled workflows with definition (for cron scheduler)."""
    workflows = workflow_service.list_scheduled_workflows()
    items = [
        {
            "id": str(w.id),
            "name": w.name,
            "definition": w.definition,
            "project_id": str(w.project_id),
            "project": {"tenant_id": str(w.project.tenant_id)} if w.project else None,
        }
        for w in workflows
    ]
    return {"items": items}


@router.get("/workflows", response_model=WorkflowListResponse, tags=["workflows"])
def list_workflows(
    project_id: UUID | None = Query(default=None),
    status_filter: WorkflowStatus | None = Query(default=None, alias="status"),
    trigger_type: WorkflowTriggerType | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowListResponse:
    items, total = workflow_service.list_workflows(
        project_id=project_id,
        status_filter=status_filter,
        trigger_type=trigger_type,
        search=search,
        limit=limit,
        offset=offset,
    )
    return WorkflowListResponse(
        items=[_build_workflow_summary(w) for w in items],
        total=total,
    )


@router.get("/workflows/{workflow_id}", response_model=WorkflowDetailResponse, tags=["workflows"])
def get_workflow(
    workflow_id: UUID,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowDetailResponse:
    workflow = workflow_service.get_workflow(workflow_id)
    return _build_workflow_detail(workflow)


@router.put("/workflows/{workflow_id}", response_model=WorkflowDetailResponse, tags=["workflows"])
def update_workflow(
    workflow_id: UUID,
    payload: WorkflowUpdateRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowDetailResponse:
    workflow = workflow_service.update_workflow(workflow_id, payload)
    return _build_workflow_detail(workflow)


@router.delete("/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["workflows"])
def delete_workflow(
    workflow_id: UUID,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> Response:
    workflow_service.delete_workflow(workflow_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/workflows/{workflow_id}/execute", response_model=WorkflowExecutionResponse, tags=["workflows"])
def execute_workflow(
    workflow_id: UUID,
    payload: WorkflowExecutionRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowExecutionResponse:
    execution = workflow_service.execute_workflow(workflow_id, payload)
    return WorkflowExecutionResponse(
        execution_id=execution.get("execution_id", str(workflow_id)),
        workflow_id=workflow_id,
        status=execution.get("status", "pending"),
    )


@router.post("/workflows/builder", response_model=WorkflowBuilderDetailResponse, status_code=status.HTTP_201_CREATED, tags=["workflow-builder"])
def create_workflow_from_builder(
    payload: WorkflowBuilderCreateRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowBuilderDetailResponse:
    """Create workflow from builder format (nodes, edges, configuration)."""
    workflow = workflow_service.create_workflow_from_builder(payload)
    return _build_workflow_builder_detail(workflow)


@router.get("/workflows/{workflow_id}/builder", response_model=WorkflowBuilderDetailResponse, tags=["workflow-builder"])
def get_workflow_builder(
    workflow_id: UUID,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowBuilderDetailResponse:
    """Get workflow in builder format (nodes, edges, configuration)."""
    workflow = workflow_service.get_workflow(workflow_id)
    return _build_workflow_builder_detail(workflow)


@router.post("/workflow/run", response_model=WorkflowExecutionResponse, tags=["workflow-builder"])
def run_workflow(
    payload: WorkflowRunRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowExecutionResponse:
    """Run a workflow. Pass workflow_id and input_payload in body."""
    execution = workflow_service.execute_workflow(
        payload.workflow_id,
        WorkflowExecutionRequest(input_payload=payload.input_payload),
    )
    return WorkflowExecutionResponse(
        execution_id=execution.get("execution_id", str(payload.workflow_id)),
        workflow_id=payload.workflow_id,
        status=execution.get("status", "pending"),
    )


@router.post("/workflows/webhooks/{path:path}", response_model=WorkflowExecutionResponse, tags=["triggers"])
async def invoke_webhook(
    path: str,
    request: Request,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowExecutionResponse | Response:
    """Incoming webhook: execute workflow by path. Body JSON is used as input_payload."""
    try:
        body = await request.json()
        input_payload = body.get("input_payload", body) if isinstance(body, dict) else {}
    except Exception:
        input_payload = {}
    execution = workflow_service.execute_workflow_by_webhook(path, input_payload)
    if execution is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND, content='{"detail":"No workflow found for webhook path"}')
    return WorkflowExecutionResponse(
        execution_id=execution.get("execution_id", ""),
        workflow_id=UUID(execution.get("workflow_id", "")),
        status=execution.get("status", "pending"),
    )


@router.post("/workflows/events", tags=["triggers"])
def trigger_events(
    payload: WorkflowEventTriggerRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    """Event trigger: when new blog created, etc. Fires all workflows matching source.event."""
    results = workflow_service.trigger_workflows_by_event(
        payload.source, payload.event, payload.payload
    )
    return {"triggered": len(results), "executions": results}
