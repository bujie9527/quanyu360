"""Tool registry: dynamic loading, registration, discovery, execution."""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from tools.runtime.base import BaseTool
from tools.runtime.base import ToolExecutionContext
from tools.runtime.base import ToolExecutionResult
from tools.runtime.loader import ToolLoader
from tools.runtime.sandbox import run_sandboxed


class ToolRegistry:
    """
    Registry for tools. Discovers and loads tools dynamically at runtime via ToolLoader.
    Tools are auto-discovered from tools/{name}/tool.py (folder per tool).
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance by name."""
        self._tools[tool.name] = tool

    def load_from_loader(
        self,
        loader: ToolLoader | None = None,
        *,
        include_plugins: bool = True,
        enabled_only: tuple[str, ...] | None = None,
    ) -> "ToolRegistry":
        """
        Load tools dynamically from tools folder using ToolLoader.
        Discovers tools/{name}/tool.py and optionally tools/plugins/*.py.
        Returns self for chaining.
        """
        ld = loader or ToolLoader()
        factories = ld.discover_factories(
            include_plugins=include_plugins,
            enabled_only=enabled_only,
        )
        for factory in factories.values():
            self.register(factory())
        return self

    def get(self, name: str) -> BaseTool:
        """Get tool by name. Raises ValueError if not found."""
        tool = self._tools.get(name)
        if tool is None:
            raise ValueError(f"Tool '{name}' is not registered.")
        return tool

    def has(self, name: str) -> bool:
        return name in self._tools

    def list_tools(self) -> list[dict[str, Any]]:
        """Return tool definitions for agent discovery (name, description, parameters/actions)."""
        return [
            tool.definition.model_dump(mode="json")
            for tool in sorted(self._tools.values(), key=lambda t: t.name)
        ]

    def execute(
        self,
        name: str,
        action: str,
        parameters: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        tool = self.get(name)
        timeout = None
        if context.metadata:
            t = context.metadata.get("tool_timeout_seconds")
            if isinstance(t, (int, float)) and t > 0:
                timeout = int(t)

        def _run() -> ToolExecutionResult:
            return tool.execute(action=action, parameters=parameters, context=context)

        return run_sandboxed(
            _run,
            tool_name=name,
            action=action,
            timeout_seconds=timeout,
        )


def clear_registry_cache() -> None:
    """Clear get_tool_registry cache. Next call reloads tools from disk."""
    get_tool_registry.cache_clear()


@lru_cache
def get_tool_registry(enabled_plugins: tuple[str, ...] | None = None) -> ToolRegistry:
    """
    Build registry via ToolLoader. Auto-discovers tools at runtime from:
      - tools/{name}/tool.py (folder-based, primary)
      - tools/plugins/{name}.py (legacy fallback)
    When enabled_plugins is None or empty, loads all discovered tools.
    When specified, loads only those tool names.
    """
    registry = ToolRegistry()
    registry.load_from_loader(
        include_plugins=True,
        enabled_only=tuple(enabled_plugins) if enabled_plugins else None,
    )
    return registry
