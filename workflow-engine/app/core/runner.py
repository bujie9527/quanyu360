from __future__ import annotations

from datetime import datetime
from datetime import timezone
from uuid import uuid4

from app.core.graph_runner import build_graph
from app.core.graph_runner import run_graph_execution
from app.core.execution_state import ExecutionState
from app.core.schemas import ExecutionCreateRequest
from app.core.schemas import WorkflowExecutionState
from app.core.state import load_execution_state
from app.core.state import save_execution_state


def create_execution_state(payload: ExecutionCreateRequest) -> WorkflowExecutionState:
    execution_id = f"wfe_{uuid4().hex}"
    ctx = {
        "input": payload.input_payload,
        "workflow_snapshot": payload.workflow.model_dump(mode="json"),
        **({"tenant_id": payload.tenant_id} if payload.tenant_id else {}),
        **({"task_run_id": payload.task_run_id} if payload.task_run_id else {}),
    }
    state = WorkflowExecutionState(
        execution_id=execution_id,
        workflow_id=payload.workflow_id,
        workflow_name=payload.workflow.name,
        status="queued",
        current_step=None,
        input_payload=payload.input_payload,
        context=ctx,
        step_history=[],
        started_at=datetime.now(timezone.utc),
        completed_at=None,
    )
    save_execution_state(state)
    return state


def _wf_state_to_execution_state(wf_state: WorkflowExecutionState) -> ExecutionState:
    """Convert persisted WorkflowExecutionState to ExecutionState."""
    from datetime import datetime as dt

    def parse_dt(v: datetime | str | None):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            return dt.fromisoformat(v.replace("Z", "+00:00"))
        return None

    return ExecutionState(
        execution_id=wf_state.execution_id,
        workflow_id=wf_state.workflow_id,
        workflow_name=wf_state.workflow_name,
        status=wf_state.status,
        input_payload=wf_state.input_payload,
        started_at=wf_state.started_at,
        current_node_id=wf_state.current_node or wf_state.current_step,
        context=dict(wf_state.context),
        node_history=[],
        error_message=wf_state.error_message,
        completed_at=parse_dt(wf_state.completed_at),
    )


def run_execution(execution_id: str, workflow_snapshot: dict[str, object]) -> WorkflowExecutionState:
    wf_state = load_execution_state(execution_id)
    if wf_state is None:
        raise ValueError(f"Execution '{execution_id}' was not found.")

    graph = build_graph(workflow_snapshot)
    exec_state = _wf_state_to_execution_state(wf_state)
    run_graph_execution(exec_state, graph, workflow_snapshot)
    result = exec_state.to_workflow_execution_state()
    save_execution_state(result)
    return result
