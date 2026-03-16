from pydantic import BaseModel

from app.core.queue import enqueue_execution
from app.core.runner import create_execution_state
from app.core.schemas import ExecutionCreateRequest


class WorkflowExecution(BaseModel):
    execution_id: str
    workflow_id: str
    broker_stream: str
    status: str


def dispatch_execution(payload: ExecutionCreateRequest, broker_stream: str) -> WorkflowExecution:
    state = create_execution_state(payload)
    enqueue_execution(state.execution_id)
    return WorkflowExecution(
        execution_id=state.execution_id,
        workflow_id=state.workflow_id,
        broker_stream=broker_stream,
        status=state.status,
    )
