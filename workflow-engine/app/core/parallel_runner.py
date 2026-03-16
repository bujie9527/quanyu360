"""Async parallel branch execution for workflow engine."""
from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import replace
from datetime import datetime
from datetime import timezone
from typing import Any

from app.core.execution_log_client import log_step_run
from app.core.execution_state import ExecutionState
from app.core.execution_state import NodeExecutionRecord
from app.core.graph import WorkflowGraph
from app.core.graph import WorkflowNode
from app.core.node_executor import NodeExecutorRegistry
from app.core.node_executor import NodeExecutionResult


def _execute_branch_sync(
    branch_id: str,
    graph: WorkflowGraph,
    registry: NodeExecutorRegistry,
    state: ExecutionState,
) -> tuple[str, NodeExecutionResult | None, NodeExecutionRecord | None, BaseException | None]:
    """
    Execute a single branch node (sync). Returns (branch_id, result, record, exception).
    """
    node = graph.get_node(branch_id)
    if node is None:
        return (branch_id, None, None, ValueError(f"Unknown branch node '{branch_id}'"))

    branch_state = replace(
        state,
        current_node_id=branch_id,
        context=deepcopy(state.context),
        node_history=[],
    )
    started_at = datetime.now(timezone.utc)
    try:
        executor = registry.get(node.type)
        result = executor.execute(node, branch_state)
        record = NodeExecutionRecord(
            node_id=node.id,
            node_type=node.type,
            status=result.status,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            output=result.output,
            next_node_ids=result.next_node_ids,
            error_message=result.error_message,
        )
        return (branch_id, result, record, None)
    except BaseException as exc:
        record = NodeExecutionRecord(
            node_id=node.id,
            node_type=node.type,
            status="failed",
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            output={},
            next_node_ids=[],
            error_message=str(exc),
        )
        return (branch_id, None, record, exc)


async def run_parallel_branches(
    state: ExecutionState,
    graph: WorkflowGraph,
    registry: NodeExecutorRegistry,
    branch_ids: list[str],
    join_next_node_id: str | None,
    fail_fast: bool,
) -> tuple[bool, str | None]:
    """
    Execute branch nodes concurrently via asyncio.
    Returns (success, next_node_id). If fail_fast and any branch fails, success=False.
    """
    if not branch_ids:
        return (True, join_next_node_id)

    loop = asyncio.get_running_loop()
    tasks = [
        loop.run_in_executor(
            None,
            _execute_branch_sync,
            bid,
            graph,
            registry,
            state,
        )
        for bid in branch_ids
    ]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    def _persist(rec: NodeExecutionRecord) -> None:
        task_run_id = state.context.get("task_run_id")
        if not task_run_id:
            return
        duration = 0.0
        if rec.started_at and rec.completed_at:
            duration = (rec.completed_at - rec.started_at).total_seconds()
        out = dict(rec.output)
        if rec.error_message:
            out["error_message"] = rec.error_message
        log_step_run(str(task_run_id), rec.node_id, rec.status, duration, out)

    failed: list[tuple[str, BaseException]] = []
    for branch_id, result, record, exc in results:
        if record:
            state.node_history.append(record)
            _persist(record)
        if exc is not None:
            failed.append((branch_id, exc))
            if fail_fast:
                for _bid, _exc in failed:
                    state.context[_bid] = {"error": str(_exc), "status": "failed"}
                first_fail = failed[0]
                state.error_message = f"Parallel branch '{first_fail[0]}' failed: {first_fail[1]}"
                return (False, None)
        elif result is not None:
            state.context[branch_id] = result.output

    if failed:
        for bid, exc in failed:
            state.context[bid] = {"error": str(exc), "status": "failed"}
        state.context["_last_output"] = {
            "parallel_results": {bid: state.context.get(bid, {}) for bid in branch_ids},
            "failed_branches": [bid for bid, _ in failed],
            "partial": True,
        }
    else:
        state.context["_last_output"] = {
            "parallel_results": {bid: state.context.get(bid, {}) for bid in branch_ids},
            "partial": False,
        }

    return (True, join_next_node_id)
