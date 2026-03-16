"""NodeExecutor: executes workflow nodes by type (start, agent, tool, condition, parallel, delay, end)."""
from __future__ import annotations

import time
from abc import ABC
from abc import abstractmethod
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.expression import evaluate_expression
from app.core.graph import WorkflowNode
from app.core.execution_state import ExecutionState
from tools.runtime import ToolExecutionContext
from tools.runtime import check_tool_rate_limit
from tools.runtime import consume_tool_rate_limit
from tools.runtime import get_tool_registry

from app.core.audit_client import log_tool_call
from common.app.usage_client import track_tool_execution
from common.app.core.logging import EVENT_AGENT_EXECUTION
from common.app.core.logging import EVENT_ERROR
from common.app.core.logging import EVENT_TOOL_EXECUTION
from common.app.core.logging import log_event


class NodeExecutionResult:
    """Result of executing a node."""

    def __init__(
        self,
        output: dict[str, Any],
        next_node_ids: list[str],
        status: str = "completed",
        error_message: str | None = None,
        join_next_node_id: str | None = None,
    ) -> None:
        self.output = output
        self.next_node_ids = next_node_ids
        self.status = status
        self.error_message = error_message
        self.join_next_node_id = join_next_node_id


class BaseNodeExecutor(ABC):
    """Base executor for workflow nodes."""

    node_type: str

    @abstractmethod
    def execute(self, node: WorkflowNode, state: ExecutionState) -> NodeExecutionResult:
        raise NotImplementedError


class StartNodeExecutor(BaseNodeExecutor):
    """start: pass-through, forwards to next_nodes."""

    node_type = "start"

    def execute(self, node: WorkflowNode, state: ExecutionState) -> NodeExecutionResult:
        output = {"input": state.input_payload, "status": "started"}
        return NodeExecutionResult(output=output, next_node_ids=list(node.next_nodes))


class AgentNodeExecutor(BaseNodeExecutor):
    """agent: calls agent-runtime."""

    node_type = "agent"

    def execute(self, node: WorkflowNode, state: ExecutionState) -> NodeExecutionResult:
        config = node.config
        agent_id = str(config.get("agent_id", config.get("assigned_agent_id", ""))).strip()
        if not agent_id:
            raise ValueError(f"Agent node '{node.id}' requires config.agent_id.")

        base_url = (get_settings().agent_runtime_url or "").rstrip("/")
        if not base_url:
            raise ValueError("agent_runtime_url is not configured.")

        task_title = config.get("task_title") or config.get("name", "Workflow task")
        task_desc = config.get("task_description") or ""
        input_payload = dict(config.get("input_payload") or {})
        prior = state.context.get("_last_output")
        if prior and isinstance(prior, dict):
            input_payload.setdefault("prior_workflow_output", prior)

        payload_body = {
            "agent_id": str(agent_id),
            "task_id": f"wf_{state.execution_id}_{node.id}",
            "task": {"title": task_title, "description": task_desc, "input_payload": input_payload},
            "metadata": {
                "workflow_id": state.workflow_id,
                "execution_id": state.execution_id,
            },
        }

        log_event(
            get_settings().service_name,
            EVENT_AGENT_EXECUTION,
            message="Workflow agent node execution started",
            execution_id=state.execution_id,
            node_key=node.id,
            agent_id=str(agent_id),
            stage="start",
        )

        from datetime import datetime, timezone
        started_at = datetime.now(timezone.utc)
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(
                    f"{base_url}/api/v1/runs",
                    json=payload_body,
                    headers={"Content-Type": "application/json"},
                )
        except httpx.ConnectError as exc:
            raise ValueError(f"Agent runtime connection failed: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise ValueError(f"Agent runtime timeout: {exc}") from exc

        if resp.status_code >= 400:
            err_text = resp.text[:500] if resp.text else ""
            raise ValueError(f"Agent runtime returned {resp.status_code}: {err_text}")

        data = resp.json()
        status_val = data.get("status", "unknown")
        result = data.get("result", {})
        content = result.get("content", "") if isinstance(result, dict) else ""
        logs = data.get("logs", [])
        tool_results = data.get("tool_results", [])
        output = {
            "agent_id": str(agent_id),
            "node_id": node.id,
            "status": status_val,
            "result": result,
            "content": content,
            "logs": logs,
            "tool_results": tool_results,
        }
        state.context.setdefault("agent_outputs", {})[node.id] = output

        if status_val != "completed":
            raise ValueError(result.get("content") or result.get("raw", {}).get("error") or f"Agent status: {status_val}")

        return NodeExecutionResult(output=output, next_node_ids=list(node.next_nodes))


class ToolNodeExecutor(BaseNodeExecutor):
    """tool: executes a tool."""

    node_type = "tool"

    def execute(self, node: WorkflowNode, state: ExecutionState) -> NodeExecutionResult:
        config = node.config
        tool_name = str(config.get("tool_name", "")).strip()
        action = str(config.get("action", "")).strip()
        if not tool_name or not action:
            raise ValueError(f"Tool node '{node.id}' requires config.tool_name and config.action.")

        registry = get_tool_registry()
        parameters = config.get("parameters") or {}
        if not isinstance(parameters, dict):
            parameters = {}
        prior = state.context.get("_last_output")
        if prior and isinstance(prior, dict):
            parameters.setdefault("content", prior.get("content", ""))
            parameters.setdefault("title", prior.get("title", prior.get("content", "")[:200]))
        else:
            input_payload = state.context.get("input") or state.input_payload or {}
            if isinstance(input_payload, dict):
                parameters.setdefault("content", input_payload.get("content", ""))
                parameters.setdefault("title", input_payload.get("title", input_payload.get("content", "")[:200]))

        connector_config = config.get("connector_config") or {}
        if not isinstance(connector_config, dict):
            connector_config = {}

        tenant_id = state.context.get("tenant_id")
        wf_snap = state.context.get("workflow_snapshot") or {}
        if not tenant_id and wf_snap.get("tenant_id"):
            tenant_id = str(wf_snap["tenant_id"])
        ctx_meta = {
            "workflow_node": node.id,
            "tool_timeout_seconds": get_settings().tool_timeout_seconds,
            "prior_output": prior if isinstance(prior, dict) else None,
        }
        settings = get_settings()
        allowed, err = check_tool_rate_limit(
            redis_url=settings.redis_url,
            redis_key_prefix=settings.rate_limit_key_prefix,
            tool_name=tool_name,
            action=action,
            tenant_id=tenant_id,
            agent_id=None,
        )
        if not allowed:
            raise ValueError(err or "Rate limit exceeded")

        log_event(
            get_settings().service_name,
            EVENT_TOOL_EXECUTION,
            message="Workflow tool node execution started",
            execution_id=state.execution_id,
            node_key=node.id,
            tool_name=tool_name,
            action=action,
            stage="start",
        )

        result = registry.execute(
            name=tool_name,
            action=action,
            parameters=parameters,
            context=ToolExecutionContext(
                agent_id=None,
                metadata=ctx_meta,
                connector_config=connector_config,
            ),
        )
        consume_tool_rate_limit(
            redis_url=settings.redis_url,
            redis_key_prefix=settings.rate_limit_key_prefix,
            tool_name=tool_name,
            action=action,
            tenant_id=tenant_id,
            agent_id=None,
        )

        if not result.success:
            if tenant_id and settings.admin_service_url:
                log_tool_call(
                    settings.admin_service_url,
                    tenant_id=tenant_id,
                    project_id=str(wf_snap.get("project_id")) if wf_snap.get("project_id") else None,
                    agent_id=None,
                    workflow_id=state.workflow_id,
                    execution_id=state.execution_id,
                    tool_name=tool_name,
                    action=action,
                    success=False,
                    node_key=node.id,
                )
                track_tool_execution(
                    settings.admin_service_url,
                    tenant_id=str(tenant_id),
                    project_id=str(wf_snap.get("project_id")) if wf_snap.get("project_id") else None,
                    tool_name=tool_name,
                    action=action,
                    workflow_id=state.workflow_id,
                    execution_id=state.execution_id,
                )
            raise ValueError(result.error_message or f"Tool '{tool_name}' action '{action}' failed.")

        if tenant_id and settings.admin_service_url:
            log_tool_call(
                settings.admin_service_url,
                tenant_id=tenant_id,
                project_id=str(wf_snap.get("project_id")) if wf_snap.get("project_id") else None,
                agent_id=None,
                workflow_id=state.workflow_id,
                execution_id=state.execution_id,
                tool_name=tool_name,
                action=action,
                success=True,
                node_key=node.id,
            )
            track_tool_execution(
                settings.admin_service_url,
                tenant_id=str(tenant_id),
                project_id=str(wf_snap.get("project_id")) if wf_snap.get("project_id") else None,
                tool_name=tool_name,
                action=action,
                workflow_id=state.workflow_id,
                execution_id=state.execution_id,
            )

        output = result.model_dump(mode="json")
        state.context.setdefault("tool_outputs", {})[node.id] = output
        return NodeExecutionResult(output=output, next_node_ids=list(node.next_nodes))


class ConditionNodeExecutor(BaseNodeExecutor):
    """
    condition: branch based on expression (==, >, <, contains).
    Config:
        expression: e.g. "article_length > 1000", "status == approved", "content contains error"
        true_next_node / true_next_step / branches[0]: node when expression is true
        false_next_node / false_next_step / branches[1]: node when expression is false
        next_nodes: [true_id, false_id] alternative
    Falls back to legacy key/equals if expression not provided.
    """

    node_type = "condition"

    def execute(self, node: WorkflowNode, state: ExecutionState) -> NodeExecutionResult:
        config = node.config
        expr = str(config.get("expression", "")).strip()

        if expr:
            matched = evaluate_expression(expr, state.context)
        else:
            key = str(config.get("key", "")).strip()
            expected = config.get("equals")
            actual = state.context
            for part in key.split("."):
                if not part:
                    continue
                if isinstance(actual, dict):
                    actual = actual.get(part)
                else:
                    actual = None
                    break
            matched = actual == expected

        true_next = config.get("true_next_node") or config.get("true_next_step")
        false_next = config.get("false_next_node") or config.get("false_next_step")
        branches = config.get("branches")
        if isinstance(branches, list) and len(branches) >= 2:
            if true_next is None:
                true_next = branches[0]
            if false_next is None:
                false_next = branches[1]
        if true_next is None and node.next_nodes:
            true_next = node.next_nodes[0]
        if false_next is None and len(node.next_nodes) > 1:
            false_next = node.next_nodes[1]
        elif false_next is None and node.next_nodes:
            false_next = node.next_nodes[0]

        chosen = true_next if matched else false_next
        next_node = str(chosen) if chosen is not None else (node.next_nodes[0] if node.next_nodes else None)
        next_ids = [next_node] if next_node else []
        output = {"expression": expr or config.get("key"), "matched": matched, "branch": "true" if matched else "false"}
        return NodeExecutionResult(output=output, next_node_ids=next_ids)


class ParallelNodeExecutor(BaseNodeExecutor):
    """
    parallel: fork to multiple branch nodes; runner executes them concurrently via asyncio.
    Config:
        branches / next_nodes: node ids to run in parallel
        join_next_node: node to continue after all branches complete
        fail_fast: if True (default), fail workflow when any branch fails
        continue_on_error: if True, proceed to join with partial results on branch failure
    """

    node_type = "parallel"

    def execute(self, node: WorkflowNode, state: ExecutionState) -> NodeExecutionResult:
        branch_ids = list(node.next_nodes)
        config = node.config
        join_next = config.get("join_next_node") or config.get("join_next_step")
        fail_fast = config.get("fail_fast", True)
        if config.get("continue_on_error"):
            fail_fast = False
        output = {
            "forked": branch_ids,
            "join_next": join_next,
            "fail_fast": fail_fast,
            "context": state.context.get("_last_output"),
        }
        return NodeExecutionResult(
            output=output,
            next_node_ids=branch_ids,
            join_next_node_id=str(join_next) if join_next else None,
        )


class DelayNodeExecutor(BaseNodeExecutor):
    """delay: sleep for N seconds."""

    node_type = "delay"

    def execute(self, node: WorkflowNode, state: ExecutionState) -> NodeExecutionResult:
        settings = get_settings()
        seconds = int(node.config.get("seconds", 1))
        effective = max(0, min(seconds, settings.max_delay_seconds))
        time.sleep(effective)
        output = {"requested_seconds": seconds, "effective_seconds": effective}
        return NodeExecutionResult(output=output, next_node_ids=list(node.next_nodes))


class EndNodeExecutor(BaseNodeExecutor):
    """end: terminal node, no next nodes."""

    node_type = "end"

    def execute(self, node: WorkflowNode, state: ExecutionState) -> NodeExecutionResult:
        output = {"status": "ended", "context": state.context.get("_last_output")}
        return NodeExecutionResult(output=output, next_node_ids=[])


class NodeExecutorRegistry:
    """Registry of node executors by type."""

    def __init__(self) -> None:
        self._executors: dict[str, BaseNodeExecutor] = {
            "start": StartNodeExecutor(),
            "agent": AgentNodeExecutor(),
            "tool": ToolNodeExecutor(),
            "condition": ConditionNodeExecutor(),
            "parallel": ParallelNodeExecutor(),
            "delay": DelayNodeExecutor(),
            "end": EndNodeExecutor(),
            "agent_node": AgentNodeExecutor(),
            "tool_node": ToolNodeExecutor(),
            "condition_node": ConditionNodeExecutor(),
            "delay_node": DelayNodeExecutor(),
            "agent_task": AgentNodeExecutor(),
            "tool_call": ToolNodeExecutor(),
        }

    def get(self, node_type: str) -> BaseNodeExecutor:
        normalized = node_type.lower().replace("_node", "").replace("_task", "").replace("_call", "")
        executor = self._executors.get(normalized) or self._executors.get(node_type)
        if executor is None:
            raise ValueError(f"Unsupported workflow node type: {node_type}")
        return executor
