"""Tool interface: name, description, parameters, execute."""
from __future__ import annotations

from typing import Any
from typing import Protocol
from typing import runtime_checkable

from tools.runtime.base import ToolActionDefinition
from tools.runtime.base import ToolDefinition
from tools.runtime.base import ToolExecutionContext
from tools.runtime.base import ToolExecutionResult


@runtime_checkable
class ToolInterface(Protocol):
    """Contract for executable tools. Agents discover tools via ToolRegistry and invoke execute()."""

    name: str
    description: str

    @property
    def definition(self) -> ToolDefinition:
        """Tool metadata: name, description, actions with parameters."""
        ...

    @property
    def actions(self) -> dict[str, ToolActionDefinition]:
        """Action definitions with parameters schema."""
        ...

    def execute(
        self,
        action: str,
        parameters: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        """Execute the given action with parameters. Returns structured result."""
        ...
