"""Node execution system: agent_node, tool_node, condition_node, delay_node."""
from __future__ import annotations

import time
from abc import ABC
from abc import abstractmethod
from datetime import datetime
from datetime import timezone
from typing import Any

import httpx

from app.core.config import get_settings
from common.app.core.logging import EVENT_AGENT_EXECUTION
from common.app.core.logging import EVENT_ERROR
from common.app.core.logging import EVENT_TOOL_EXECUTION
from common.app.core.logging import log_event
from app.core.schemas import NodeType
from app.core.schemas import StepExecutionResult
from app.core.schemas import WorkflowNode
from tools.runtime import ToolExecutionContext
from tools.runtime import check_tool_rate_limit
from tools.runtime import consume_tool_rate_limit
from tools.runtime import get_tool_registry

from app.core.audit_client import log_tool_call


class BaseNodeExecutor(ABC):
    """Base executor for workflow nodes."""

    node_type: str

    @abstractmethod
    def execute(self, node: WorkflowNode, context: dict[str, Any]) -> StepExecutionResult:
        raise NotImplementedError


class AgentNodeExecutor(BaseNodeExecutor):
    """Execute agent_node: calls agent-runtime to run an agent task."""

    node_type = NodeType.agent_node.value

    def execute(self, node: WorkflowNode, context: dict[str, Any]) -> StepExecutionResult:
        agent_id = node.assigned_agent_id or str(node.config.get("agent_id", ""))
        if not agent_id:
            raise ValueError(f"Agent node '{node.node_key}' requires assigned_agent_id or config.agent_id.")

        base_url = (get_settings().agent_runtime_url or "").rstrip("/")
        if not base_url:
            raise ValueError("agent_runtime_url is not configured.")

        task_title = node.config.get("task_title") or node.name
        task_desc = node.config.get("task_description") or ""
        input_payload = dict(node.config.get("input_payload") or {})
        wf_snapshot = context.get("workflow_snapshot") or {}
        project_id = str(node.config.get("project_id") or wf_snapshot.get("project_id", ""))
        execution_id = str(context.get("execution_id", ""))
        prior_output = context.get("_last_output")
        if prior_output and isinstance(prior_output, dict):
            input_payload.setdefault("prior_workflow_output", prior_output)

        payload_body = {
            "agent_id": str(agent_id),
            "task_id": f"wf_{execution_id}_{node.node_key}",
            "task": {
                "title": task_title,
                "description": task_desc,
                "input_payload": input_payload,
            },
            "metadata": {
                "workflow_id": node.workflow_id,
                "project_id": project_id,
                "node_key": node.node_key,
            },
        }

        log_event(
            get_settings().service_name,
            EVENT_AGENT_EXECUTION,
            message="Workflow agent node execution started",
            execution_id=execution_id,
            node_key=node.node_key,
            agent_id=str(agent_id),
            stage="start",
        )
        started_at = datetime.now(timezone.utc)
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(
                    f"{base_url}/api/v1/runs",
                    json=payload_body,
                    headers={"Content-Type": "application/json"},
                )
        except httpx.ConnectError as exc:
            log_event(
                get_settings().service_name,
                EVENT_ERROR,
                level="error",
                message=str(exc),
                execution_id=execution_id,
                node_key=node.node_key,
                agent_id=str(agent_id),
                error=str(exc),
            )
            raise ValueError(f"Agent runtime connection failed: {exc}") from exc
        except httpx.TimeoutException as exc:
            log_event(
                get_settings().service_name,
                EVENT_ERROR,
                level="error",
                message=str(exc),
                execution_id=execution_id,
                node_key=node.node_key,
                agent_id=str(agent_id),
                error=str(exc),
            )
            raise ValueError(f"Agent runtime timeout: {exc}") from exc

        if resp.status_code >= 400:
            err_text = resp.text[:500] if resp.text else ""
            raise ValueError(f"Agent runtime returned {resp.status_code}: {err_text}")

        data = resp.json()
        status_val = data.get("status", "unknown")
        result = data.get("result", {})
        content = result.get("content", "") if isinstance(result, dict) else ""
        duration_ms = (datetime.now(timezone.utc) - started_at).total_seconds() * 1000
        log_event(
            get_settings().service_name,
            EVENT_AGENT_EXECUTION,
            message="Workflow agent node execution finished",
            execution_id=execution_id,
            node_key=node.node_key,
            agent_id=str(agent_id),
            status=status_val,
            duration_ms=round(duration_ms, 2),
            stage="finish",
        )
        output = {
            "agent_id": str(agent_id),
            "node_key": node.node_key,
            "status": status_val,
            "result": result,
            "content": content,
        }
        context.setdefault("agent_outputs", {})[node.node_key] = output
        if status_val != "completed":
            raise ValueError(result.get("content") or result.get("raw", {}).get("error") or f"Agent status: {status_val}")

        return StepExecutionResult(status="completed", output=output, next_step=node.next_node)


class ToolNodeExecutor(BaseNodeExecutor):
    """Execute tool_node: runs a tool (e.g. wordpress, facebook)."""

    node_type = NodeType.tool_node.value

    def execute(self, node: WorkflowNode, context: dict[str, Any]) -> StepExecutionResult:
        tool_name = str(node.config.get("tool_name", "")).strip()
        action = str(node.config.get("action", "")).strip()
        if not tool_name or not action:
            raise ValueError(
                f"Tool node '{node.node_key}' requires config.tool_name and config.action "
                "(e.g. tool_name='wordpress', action='publish_post')."
            )

        registry = get_tool_registry()
        parameters = node.config.get("parameters", {})
        if not isinstance(parameters, dict):
            parameters = {}

        prior_output = context.get("_last_output")
        if prior_output and isinstance(prior_output, dict) and "content" in prior_output:
            parameters.setdefault("content", prior_output.get("content", ""))
        if prior_output and isinstance(prior_output, dict) and "title" in prior_output:
            parameters.setdefault("title", prior_output.get("title", prior_output.get("content", "")[:200]))

        connector_config = node.config.get("connector_config") or {}
        if not isinstance(connector_config, dict):
            connector_config = {}

        execution_id = str(context.get("execution_id", ""))
        wf_snapshot = context.get("workflow_snapshot") or {}
        tenant_id = context.get("tenant_id") or (str(wf_snapshot.get("tenant_id")) if wf_snapshot.get("tenant_id") else None)
        agent_id = str(node.assigned_agent_id) if node.assigned_agent_id else None
        settings = get_settings()
        allowed, err = check_tool_rate_limit(
            redis_url=settings.redis_url,
            redis_key_prefix=settings.rate_limit_key_prefix,
            tool_name=tool_name,
            action=action,
            tenant_id=tenant_id,
            agent_id=agent_id,
        )
        if not allowed:
            raise ValueError(err or "Rate limit exceeded")
        log_event(
            get_settings().service_name,
            EVENT_TOOL_EXECUTION,
            message="Workflow tool node execution started",
            execution_id=execution_id,
            node_key=node.node_key,
            tool_name=tool_name,
            action=action,
            stage="start",
        )
        started_at = datetime.now(timezone.utc)
        result = registry.execute(
            name=tool_name,
            action=action,
            parameters=parameters,
            context=ToolExecutionContext(
                agent_id=node.assigned_agent_id,
                metadata={"workflow_node": node.node_key, "tool_id": node.tool_id},
                connector_config=connector_config,
            ),
        )
        consume_tool_rate_limit(
            redis_url=settings.redis_url,
            redis_key_prefix=settings.rate_limit_key_prefix,
            tool_name=tool_name,
            action=action,
            tenant_id=tenant_id,
            agent_id=agent_id,
        )
        duration_ms = (datetime.now(timezone.utc) - started_at).total_seconds() * 1000
        if not result.success:
            log_event(
                get_settings().service_name,
                EVENT_TOOL_EXECUTION,
                level="error",
                message=f"Tool {tool_name}:{action} failed",
                execution_id=execution_id,
                node_key=node.node_key,
                tool_name=tool_name,
                action=action,
                duration_ms=round(duration_ms, 2),
                success=False,
                error=result.error_message,
                stage="finish",
            )
            log_event(
                get_settings().service_name,
                EVENT_ERROR,
                level="error",
                message=result.error_message or "Tool execution failed",
                execution_id=execution_id,
                node_key=node.node_key,
                tool_name=tool_name,
                action=action,
                error=result.error_message,
            )
            if tenant_id and settings.admin_service_url:
                log_tool_call(
                    settings.admin_service_url,
                    tenant_id=tenant_id,
                    project_id=str(wf_snapshot.get("project_id")) if wf_snapshot.get("project_id") else None,
                    agent_id=agent_id,
                    workflow_id=str(node.workflow_id) if node.workflow_id else None,
                    execution_id=execution_id,
                    tool_name=tool_name,
                    action=action,
                    success=False,
                    node_key=node.node_key,
                )
            raise ValueError(result.error_message or f"Tool '{tool_name}' action '{action}' failed.")

        if tenant_id and settings.admin_service_url:
            log_tool_call(
                settings.admin_service_url,
                tenant_id=tenant_id,
                project_id=str(wf_snapshot.get("project_id")) if wf_snapshot.get("project_id") else None,
                agent_id=agent_id,
                workflow_id=str(node.workflow_id) if node.workflow_id else None,
                execution_id=execution_id,
                tool_name=tool_name,
                action=action,
                success=True,
                node_key=node.node_key,
            )
        log_event(
            get_settings().service_name,
            EVENT_TOOL_EXECUTION,
            message=f"Tool {tool_name}:{action} executed",
            execution_id=execution_id,
            node_key=node.node_key,
            tool_name=tool_name,
            action=action,
            duration_ms=round(duration_ms, 2),
            success=True,
            stage="finish",
        )
        output = result.model_dump(mode="json")
        context.setdefault("tool_outputs", {})[node.node_key] = output
        return StepExecutionResult(status="completed", output=output, next_step=node.next_node)


class ConditionNodeExecutor(BaseNodeExecutor):
    """Execute condition_node: branch based on context value."""

    node_type = NodeType.condition_node.value

    def execute(self, node: WorkflowNode, context: dict[str, Any]) -> StepExecutionResult:
        key = str(node.config.get("key", "")).strip()
        expected = node.config.get("equals")
        actual = context
        for part in key.split("."):
            if not part:
                continue
            if isinstance(actual, dict):
                actual = actual.get(part)
            else:
                actual = None
                break
        matched = actual == expected
        next_node = node.config.get("true_next_step") or node.config.get("true_next_node")
        if not matched:
            next_node = node.config.get("false_next_step") or node.config.get("false_next_node")
        if next_node is None:
            next_node = node.next_node

        output = {"key": key, "expected": expected, "actual": actual, "matched": matched}
        return StepExecutionResult(status="completed", output=output, next_step=next_node)


class DelayNodeExecutor(BaseNodeExecutor):
    """Execute delay_node: sleep for N seconds."""

    node_type = NodeType.delay_node.value

    def execute(self, node: WorkflowNode, context: dict[str, Any]) -> StepExecutionResult:
        settings = get_settings()
        seconds = int(node.config.get("seconds", 1))
        effective_seconds = max(0, min(seconds, settings.max_delay_seconds))
        time.sleep(effective_seconds)
        output = {"requested_seconds": seconds, "effective_seconds": effective_seconds}
        return StepExecutionResult(status="completed", output=output, next_step=node.next_node)


class NodeExecutorRegistry:
    """Registry of node executors by node type."""

    def __init__(self) -> None:
        self._executors: dict[str, BaseNodeExecutor] = {
            NodeType.agent_node.value: AgentNodeExecutor(),
            NodeType.tool_node.value: ToolNodeExecutor(),
            NodeType.condition_node.value: ConditionNodeExecutor(),
            NodeType.delay_node.value: DelayNodeExecutor(),
            "agent_task": AgentNodeExecutor(),
            "tool_call": ToolNodeExecutor(),
            "condition": ConditionNodeExecutor(),
            "delay": DelayNodeExecutor(),
        }

    def get(self, node_type: str) -> BaseNodeExecutor:
        executor = self._executors.get(node_type)
        if executor is None:
            raise ValueError(f"Unsupported workflow node type: {node_type}")
        return executor
