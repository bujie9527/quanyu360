from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import ClassVar

from pydantic import BaseModel
from pydantic import Field


class ToolParameterDefinition(BaseModel):
    name: str
    type: str
    required: bool = True
    description: str


class ToolActionDefinition(BaseModel):
    name: str
    description: str
    parameters: list[ToolParameterDefinition] = Field(default_factory=list)


class ToolDefinition(BaseModel):
    name: str
    description: str
    actions: list[ToolActionDefinition] = Field(default_factory=list)


class ToolExecutionContext(BaseModel):
    agent_id: str | None = None
    task_id: str | None = None
    project_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    connector_config: dict[str, Any] = Field(default_factory=dict)


class ToolExecutionResult(BaseModel):
    tool_name: str
    action: str
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None


class BaseTool(ABC):
    name: str
    description: str

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            actions=[action for action in self.actions.values()],
        )

    @property
    @abstractmethod
    def actions(self) -> dict[str, ToolActionDefinition]:
        raise NotImplementedError

    @abstractmethod
    def execute(self, action: str, parameters: dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        raise NotImplementedError


class StructuredTool(BaseTool, ABC):
    action_models: ClassVar[dict[str, type[BaseModel]]] = {}

    def execute(self, action: str, parameters: dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        model = self.action_models.get(action)
        if model is None:
            return ToolExecutionResult(
                tool_name=self.name,
                action=action,
                success=False,
                error_message=f"Unsupported action '{action}' for tool '{self.name}'.",
            )

        payload = model.model_validate(parameters)
        return self.handle(action=action, payload=payload, context=context)

    @abstractmethod
    def handle(self, action: str, payload: BaseModel, context: ToolExecutionContext) -> ToolExecutionResult:
        raise NotImplementedError
