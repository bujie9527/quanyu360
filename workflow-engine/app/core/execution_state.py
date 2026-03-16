"""ExecutionState: mutable execution state for node-based workflow run."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from app.core.schemas import WorkflowExecutionState


@dataclass
class NodeExecutionRecord:
    """Record of a single node execution."""

    node_id: str
    node_type: str
    status: str
    started_at: datetime
    completed_at: datetime | None
    output: dict[str, Any]
    next_node_ids: list[str]
    error_message: str | None = None


@dataclass
class ExecutionState:
    """
    Mutable execution state for workflow run.
    Tracks current node, context, history, status.
    """

    execution_id: str
    workflow_id: str
    workflow_name: str
    status: str
    input_payload: dict[str, Any]
    started_at: datetime

    current_node_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    node_history: list[NodeExecutionRecord] = field(default_factory=list)
    error_message: str | None = None
    completed_at: datetime | None = None

    # For parallel: tracks which branches are done
    parallel_pending: set[str] = field(default_factory=set)
    parallel_results: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_workflow_execution_state(self) -> "WorkflowExecutionState":
        """Convert to WorkflowExecutionState for Redis persistence."""
        from app.core.schemas import StepExecutionRecord
        from app.core.schemas import WorkflowExecutionState

        return WorkflowExecutionState(
            execution_id=self.execution_id,
            workflow_id=self.workflow_id,
            workflow_name=self.workflow_name,
            status=self.status,
            current_step=self.current_node_id,
            current_node=self.current_node_id,
            input_payload=self.input_payload,
            context=self.context,
            step_history=[
                StepExecutionRecord(
                    step_key=r.node_id,
                    step_type=r.node_type,
                    status=r.status,
                    started_at=r.started_at,
                    completed_at=r.completed_at,
                    output=r.output,
                    next_step=r.next_node_ids[0] if r.next_node_ids else None,
                    error_message=r.error_message,
                )
                for r in self.node_history
            ],
            error_message=self.error_message,
            started_at=self.started_at,
            completed_at=self.completed_at,
        )
