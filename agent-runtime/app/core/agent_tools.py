from __future__ import annotations

from typing import Any

from app.core.tooling import execute_registered_tool


def execute_agent_tool_calls(
    *,
    agent_id: str,
    task_id: str,
    tool_calls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for call in tool_calls:
        result = execute_registered_tool(
            tool_name=call["tool_name"],
            action=call["action"],
            parameters=call.get("parameters", {}),
            agent_id=agent_id,
            task_id=task_id,
            project_id=call.get("project_id"),
            metadata=call.get("metadata", {}),
        )
        results.append(result.model_dump(mode="json"))
    return results
