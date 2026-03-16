"""Tool execution component: runs planned tool calls and collects results."""
from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any

import structlog

from app.core.audit_client import log_tool_call
from common.app.usage_client import track_tool_execution
from app.core.config import get_settings
from common.app.core.logging import EVENT_ERROR
from common.app.core.logging import EVENT_TOOL_EXECUTION
from common.app.core.logging import log_event
from app.core.schemas import ExecutionLogEntry
from app.core.schemas import PlannedToolCall
from app.core.tooling import execute_registered_tool


class ToolExecutor:
    """Executes planned tool calls and returns structured results."""

    def __init__(self) -> None:
        self.logger = structlog.get_logger(get_settings().service_name).bind(component="tool-executor")

    def execute(
        self,
        *,
        agent_id: str,
        task_id: str,
        tool_calls: list[PlannedToolCall],
        metadata: dict[str, Any] | None = None,
        logs: list[ExecutionLogEntry] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Execute tool calls in order.
        Tool selection (from plan) → Tool execution → Results.
        """
        results: list[dict[str, Any]] = []

        log_event(
            get_settings().service_name,
            EVENT_TOOL_EXECUTION,
            message="Tool execution started",
            agent_id=agent_id,
            task_id=task_id,
            tool_calls_count=len(tool_calls),
            tools=[f"{c.tool_name}:{c.action}" for c in tool_calls],
            stage="start",
        )
        self._log(
            logs,
            stage="tool_execution_start",
            level="info",
            message="Tool execution started.",
            details={
                "agent_id": agent_id,
                "task_id": task_id,
                "tool_calls_count": len(tool_calls),
                "tools": [f"{c.tool_name}:{c.action}" for c in tool_calls],
            },
        )

        for idx, call in enumerate(tool_calls):
            call_started = datetime.now(timezone.utc)
            try:
                run_meta = dict(metadata or {})
                run_meta.update(call.metadata)
                if call.rationale:
                    run_meta["rationale"] = call.rationale
                result = execute_registered_tool(
                    tool_name=call.tool_name,
                    action=call.action,
                    parameters=call.parameters,
                    agent_id=agent_id,
                    task_id=task_id,
                    project_id=call.project_id,
                    metadata=run_meta,
                )
                result_dict = result.model_dump(mode="json")
                results.append(result_dict)

                _tid = run_meta.get("tenant_id") if isinstance(run_meta.get("tenant_id"), str) else None
                _pid = run_meta.get("project_id") or call.project_id
                if _tid and get_settings().admin_service_url:
                    log_tool_call(
                        get_settings().admin_service_url,
                        tenant_id=_tid,
                        project_id=str(_pid) if _pid else None,
                        agent_id=agent_id,
                        task_id=task_id,
                        tool_name=call.tool_name,
                        action=call.action,
                        success=result.success,
                        correlation_id=task_id,
                    )
                    track_tool_execution(
                        get_settings().admin_service_url,
                        tenant_id=_tid,
                        project_id=str(_pid) if _pid else None,
                        tool_name=call.tool_name,
                        action=call.action,
                        agent_id=agent_id,
                        task_id=task_id,
                    )
                duration_ms = (datetime.now(timezone.utc) - call_started).total_seconds() * 1000
                log_event(
                    get_settings().service_name,
                    EVENT_TOOL_EXECUTION,
                    message=f"Tool {call.tool_name}:{call.action} executed",
                    agent_id=agent_id,
                    task_id=task_id,
                    tool_name=call.tool_name,
                    action=call.action,
                    duration_ms=round(duration_ms, 2),
                    success=True,
                    stage="finish",
                )
                self._log(
                    logs,
                    stage="tool_call_complete",
                    level="info",
                    message=f"Tool {call.tool_name}:{call.action} executed.",
                    details={
                        "agent_id": agent_id,
                        "task_id": task_id,
                        "index": idx,
                        "tool_name": call.tool_name,
                        "action": call.action,
                        "duration_ms": round(duration_ms, 2),
                        "success": True,
                    },
                )
                self.logger.info(
                    "Tool executed.",
                    tool_name=call.tool_name,
                    action=call.action,
                    agent_id=agent_id,
                    task_id=task_id,
                    duration_ms=round(duration_ms, 2),
                    stage="tool_call",
                )
            except Exception as exc:
                duration_ms = (datetime.now(timezone.utc) - call_started).total_seconds() * 1000
                log_event(
                    get_settings().service_name,
                    EVENT_TOOL_EXECUTION,
                    level="error",
                    message=f"Tool {call.tool_name}:{call.action} failed",
                    agent_id=agent_id,
                    task_id=task_id,
                    tool_name=call.tool_name,
                    action=call.action,
                    duration_ms=round(duration_ms, 2),
                    success=False,
                    error=str(exc),
                    stage="finish",
                )
                log_event(
                    get_settings().service_name,
                    EVENT_ERROR,
                    level="error",
                    message=str(exc),
                    agent_id=agent_id,
                    task_id=task_id,
                    tool_name=call.tool_name,
                    action=call.action,
                    error=str(exc),
                )
                _m = metadata or {}
                _tid = _m.get("tenant_id") if isinstance(_m.get("tenant_id"), str) else None
                _pid = _m.get("project_id") or (call.project_id if hasattr(call, "project_id") else None)
                if _tid and get_settings().admin_service_url:
                    log_tool_call(
                        get_settings().admin_service_url,
                        tenant_id=_tid,
                        project_id=str(_pid) if _pid else None,
                        agent_id=agent_id,
                        task_id=task_id,
                        tool_name=call.tool_name,
                        action=call.action,
                        success=False,
                        correlation_id=task_id,
                    )
                    track_tool_execution(
                        get_settings().admin_service_url,
                        tenant_id=_tid,
                        project_id=str(_pid) if _pid else None,
                        tool_name=call.tool_name,
                        action=call.action,
                        agent_id=agent_id,
                        task_id=task_id,
                    )
                self._log(
                    logs,
                    stage="tool_call_failed",
                    level="error",
                    message=f"Tool {call.tool_name}:{call.action} failed.",
                    details={
                        "agent_id": agent_id,
                        "task_id": task_id,
                        "index": idx,
                        "tool_name": call.tool_name,
                        "action": call.action,
                        "duration_ms": round(duration_ms, 2),
                        "error": str(exc),
                        "success": False,
                    },
                )
                self.logger.error(
                    "Tool execution failed.",
                    tool_name=call.tool_name,
                    action=call.action,
                    agent_id=agent_id,
                    task_id=task_id,
                    error=str(exc),
                    stage="tool_call",
                )
                results.append({
                    "success": False,
                    "error": str(exc),
                    "tool_name": call.tool_name,
                    "action": call.action,
                })

        self._log(
            logs,
            stage="tool_execution_complete",
            level="info",
            message="Tool execution completed.",
            details={
                "agent_id": agent_id,
                "task_id": task_id,
                "tool_results_count": len(results),
            },
        )

        return results

    def _log(
        self,
        logs: list[ExecutionLogEntry] | None,
        *,
        stage: str,
        level: str,
        message: str,
        details: dict[str, Any],
    ) -> None:
        if logs is None:
            return
        logs.append(
            ExecutionLogEntry(
                stage=stage,
                level=level,
                message=message,
                timestamp=datetime.now(timezone.utc),
                details=details,
            )
        )
