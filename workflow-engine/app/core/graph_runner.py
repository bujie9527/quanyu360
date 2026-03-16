"""Graph-based workflow runner: WorkflowGraph + ExecutionState + NodeExecutor."""
from __future__ import annotations

import asyncio
from datetime import datetime
from datetime import timezone
from typing import Any

from app.core.audit_client import log_workflow_execution
from app.core.execution_log_client import log_step_run
from app.core.execution_log_client import update_task_run_status
from common.app.usage_client import track_workflow_run
from app.core.config import get_settings
from app.core.execution_state import ExecutionState
from app.core.execution_state import NodeExecutionRecord
from app.core.graph import WorkflowGraph
from app.core.graph import WorkflowNode
from app.core.node_executor import NodeExecutorRegistry
from app.core.node_executor import NodeExecutionResult
from app.core.parallel_runner import run_parallel_branches
from common.app.core.logging import EVENT_ERROR
from common.app.core.logging import log_event


def _normalize_definition(workflow_snapshot: dict[str, Any]) -> dict[str, Any]:
    """Extract definition/nodes from workflow snapshot."""
    definition = workflow_snapshot.get("definition") or workflow_snapshot
    nodes = definition.get("nodes") or definition.get("steps") or workflow_snapshot.get("steps") or []
    if not nodes and "steps" in workflow_snapshot:
        nodes = workflow_snapshot["steps"]
    config = definition.get("configuration") or {}
    entry_id = config.get("entry_node_id") or definition.get("entry_node_id")
    return {"nodes": nodes, "entry_node_id": entry_id, "configuration": config}


def _nodes_from_legacy(steps: list[Any]) -> list[dict[str, Any]]:
    """Convert legacy steps to node format."""
    out = []
    step_map = {s.get("step_key", s.get("node_key", str(i))): i for i, s in enumerate(steps) if isinstance(s, dict)}
    for i, s in enumerate(steps):
        if not isinstance(s, dict):
            continue
        node_key = str(s.get("step_key", s.get("node_key", f"node_{i}")))
        next_step = s.get("next_step") or s.get("next_node")
        out.append({
            "id": node_key,
            "node_key": node_key,
            "type": s.get("type", s.get("node_type", "agent_task")),
            "config": s.get("config", {}),
            "next_nodes": [next_step] if next_step else [],
            "name": s.get("name", node_key),
            "sequence": s.get("sequence", i),
        })
    return out


def _persist_step_run(state: ExecutionState, record: NodeExecutionRecord) -> None:
    """Write step to StepRun if task_run_id in context."""
    task_run_id = state.context.get("task_run_id")
    if not task_run_id:
        return
    duration = 0.0
    if record.started_at and record.completed_at:
        duration = (record.completed_at - record.started_at).total_seconds()
    output = dict(record.output)
    if record.error_message:
        output["error_message"] = record.error_message
    log_step_run(
        task_run_id=str(task_run_id),
        step_name=record.node_id,
        status=record.status,
        duration=duration,
        output=output,
    )


def _finalize_task_run(state: ExecutionState, status: str, completed_at: datetime) -> None:
    """Update TaskRun status/end_time when workflow finishes."""
    task_run_id = state.context.get("task_run_id")
    if not task_run_id:
        return
    update_task_run_status(
        task_run_id=str(task_run_id),
        status=status,
        end_time=completed_at.isoformat(),
    )


def build_graph(workflow_snapshot: dict[str, Any]) -> WorkflowGraph:
    """Build WorkflowGraph from workflow snapshot."""
    definition = _normalize_definition(workflow_snapshot)
    nodes_raw = definition.get("nodes") or []
    if not nodes_raw and workflow_snapshot.get("steps"):
        nodes_raw = _nodes_from_legacy(workflow_snapshot["steps"])

    graph = WorkflowGraph()
    for item in nodes_raw:
        if isinstance(item, dict):
            node = WorkflowNode.from_dict(item)
        else:
            node = WorkflowNode.from_dict(item.model_dump(mode="json"))
        graph.add_node(node)

    entry_id = definition.get("entry_node_id")
    if not entry_id and graph._nodes:
        first = list(graph._nodes.values())[0]
        entry_id = first.id
    if entry_id:
        graph.set_entry(str(entry_id))
    return graph


def run_graph_execution(
    state: ExecutionState,
    graph: WorkflowGraph,
    workflow_snapshot: dict[str, Any],
) -> ExecutionState:
    """Run workflow using graph-based execution."""
    registry = NodeExecutorRegistry()
    settings = get_settings()
    state.context["execution_id"] = state.execution_id
    state.context["workflow_snapshot"] = workflow_snapshot
    state.context["input"] = state.input_payload
    tenant_id = state.context.get("tenant_id") or str(workflow_snapshot.get("tenant_id", "")) or None
    project_id = str(workflow_snapshot.get("project_id", "")) if workflow_snapshot.get("project_id") else None

    if tenant_id and settings.admin_service_url:
        log_workflow_execution(
            settings.admin_service_url,
            tenant_id=tenant_id,
            project_id=project_id or None,
            workflow_id=state.workflow_id,
            execution_id=state.execution_id,
            status="started",
        )

    entry = graph.get_entry_node()
    if entry is None:
        state.status = "completed"
        state.completed_at = datetime.now(timezone.utc)
        return state

    current_node: WorkflowNode | None = entry
    state.status = "running"

    while current_node is not None:
        state.current_node_id = current_node.id
        started_at = datetime.now(timezone.utc)

        executor = registry.get(current_node.type)
        result: NodeExecutionResult
        try:
            result = executor.execute(current_node, state)
        except Exception as exc:
            log_event(
                settings.service_name,
                EVENT_ERROR,
                level="error",
                message=str(exc),
                execution_id=state.execution_id,
                node_key=current_node.id,
                node_type=current_node.type,
                error=str(exc),
            )
            completed_at = datetime.now(timezone.utc)
            record = NodeExecutionRecord(
                node_id=current_node.id,
                node_type=current_node.type,
                status="failed",
                started_at=started_at,
                completed_at=completed_at,
                output={},
                next_node_ids=[],
                error_message=str(exc),
            )
            state.node_history.append(record)
            _persist_step_run(state, record)
            state.status = "failed"
            state.error_message = str(exc)
            state.completed_at = datetime.now(timezone.utc)
            if tenant_id and settings.admin_service_url:
                log_workflow_execution(
                    settings.admin_service_url,
                    tenant_id=tenant_id,
                    project_id=project_id or None,
                    workflow_id=state.workflow_id,
                    execution_id=state.execution_id,
                    status="failed",
                    payload={"error": str(exc), "node_id": current_node.id},
                )
                track_workflow_run(
                    settings.admin_service_url,
                    tenant_id=tenant_id,
                    project_id=project_id or None,
                    workflow_id=state.workflow_id,
                    execution_id=state.execution_id,
                    status="failed",
                )
            _finalize_task_run(state, "failed", completed_at)
            return state

        state.context[current_node.id] = result.output
        state.context["_last_output"] = result.output
        record = NodeExecutionRecord(
            node_id=current_node.id,
            node_type=current_node.type,
            status=result.status,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            output=result.output,
            next_node_ids=result.next_node_ids,
            error_message=result.error_message,
        )
        state.node_history.append(record)
        _persist_step_run(state, record)

        if not result.next_node_ids:
            break

        join_next = getattr(result, "join_next_node_id", None) or result.output.get("join_next")
        is_parallel = len(result.next_node_ids) > 1
        if is_parallel and result.next_node_ids:
            fail_fast = result.output.get("fail_fast", True)
            success, next_id = asyncio.run(
                run_parallel_branches(
                    state,
                    graph,
                    registry,
                    result.next_node_ids,
                    str(join_next) if join_next else None,
                    fail_fast,
                ),
            )
            if not success:
                state.status = "failed"
                if not state.error_message:
                    state.error_message = "One or more parallel branches failed."
                state.completed_at = datetime.now(timezone.utc)
                if tenant_id and settings.admin_service_url:
                    log_workflow_execution(
                        settings.admin_service_url,
                        tenant_id=tenant_id,
                        project_id=project_id or None,
                        workflow_id=state.workflow_id,
                        execution_id=state.execution_id,
                        status="failed",
                        payload={"error": state.error_message},
                    )
                    track_workflow_run(
                        settings.admin_service_url,
                        tenant_id=tenant_id,
                        project_id=project_id or None,
                        workflow_id=state.workflow_id,
                        execution_id=state.execution_id,
                        status="failed",
                    )
                _finalize_task_run(state, "failed", state.completed_at or datetime.now(timezone.utc))
                return state
            current_node = graph.get_node(next_id) if next_id else None
            if current_node is None and next_id:
                state.status = "failed"
                state.error_message = f"Unknown join node '{next_id}'."
                state.completed_at = datetime.now(timezone.utc)
                _finalize_task_run(state, "failed", state.completed_at)
                return state
            if current_node is None:
                break
        else:
            next_id = result.next_node_ids[0]
            current_node = graph.get_node(next_id)
        if current_node is None:
            state.status = "failed"
            state.error_message = f"Unknown next node '{next_id}'."
            state.completed_at = datetime.now(timezone.utc)
            _finalize_task_run(state, "failed", state.completed_at)
            return state

    state.status = "completed"
    state.current_node_id = None
    state.completed_at = datetime.now(timezone.utc)
    if tenant_id and settings.admin_service_url:
        log_workflow_execution(
            settings.admin_service_url,
            tenant_id=tenant_id,
            project_id=project_id or None,
            workflow_id=state.workflow_id,
            execution_id=state.execution_id,
            status="completed",
        )
        track_workflow_run(
            settings.admin_service_url,
            tenant_id=tenant_id,
            project_id=project_id or None,
            workflow_id=state.workflow_id,
            execution_id=state.execution_id,
            status="completed",
        )
    _finalize_task_run(state, "completed", state.completed_at or datetime.now(timezone.utc))
    return state
