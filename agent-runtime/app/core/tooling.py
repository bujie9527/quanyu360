from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from tools.runtime import check_tool_rate_limit
from tools.runtime import consume_tool_rate_limit
from tools.runtime import ToolExecutionContext
from tools.runtime import ToolExecutionResult
from tools.runtime import get_tool_registry


def get_runtime_tool_registry():
    settings = get_settings()
    return get_tool_registry(tuple(settings.enabled_tool_plugins))


def list_registered_tools(allowed_slugs: list[str] | None = None) -> list[dict[str, Any]]:
    """List tools. When allowed_slugs is set, return only tools in that list."""
    items = get_runtime_tool_registry().list_tools()
    if allowed_slugs is None or not allowed_slugs:
        return items
    slug_set = {s.strip().lower() for s in allowed_slugs if isinstance(s, str)}
    return [t for t in items if (t.get("name") or "").strip().lower() in slug_set]


def execute_registered_tool(
    tool_name: str,
    action: str,
    parameters: dict[str, Any],
    *,
    agent_id: str | None = None,
    task_id: str | None = None,
    project_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ToolExecutionResult:
    settings = get_settings()
    meta = metadata or {}
    tenant_id = meta.get("tenant_id") if isinstance(meta.get("tenant_id"), str) else None

    allowed_slugs = meta.get("allowed_tool_slugs")
    if allowed_slugs is not None and isinstance(allowed_slugs, list):
        tool_slug = tool_name.strip().lower()
        if tool_slug not in {s.strip().lower() for s in allowed_slugs if isinstance(s, str)}:
            return ToolExecutionResult(
                tool_name=tool_name,
                action=action,
                success=False,
                output={},
                error_message=f"Agent is not allowed to use tool '{tool_name}'.",
            )

    allowed, err = check_tool_rate_limit(
        redis_url=settings.redis_url,
        redis_key_prefix=settings.analytics_key_prefix,
        tool_name=tool_name,
        action=action,
        tenant_id=tenant_id,
        agent_id=agent_id,
    )
    if not allowed:
        return ToolExecutionResult(
            tool_name=tool_name,
            action=action,
            success=False,
            output={},
            error_message=err or "Rate limit exceeded",
        )

    registry = get_runtime_tool_registry()
    ctx_meta = dict(metadata or {})
    ctx_meta["tool_timeout_seconds"] = settings.tool_timeout_seconds
    context = ToolExecutionContext(
        agent_id=agent_id,
        task_id=task_id,
        project_id=project_id,
        metadata=ctx_meta,
    )
    result = registry.execute(name=tool_name, action=action, parameters=parameters, context=context)
    consume_tool_rate_limit(
        redis_url=settings.redis_url,
        redis_key_prefix=settings.analytics_key_prefix,
        tool_name=tool_name,
        action=action,
        tenant_id=tenant_id,
        agent_id=agent_id,
    )
    return result
