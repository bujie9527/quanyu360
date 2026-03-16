"""AgentRun HTTP endpoints - ingest from AgentRuntime."""
from __future__ import annotations

import uuid

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from app.dependencies import get_db_session
from app.repositories.agent_run_repository import AgentRunRepository
from common.app.models import AgentRun
from pydantic import BaseModel
from pydantic import Field
from sqlalchemy.orm import Session


class AgentRunIngestRequest(BaseModel):
    agent_id: str = Field(..., description="Agent instance ID")
    type: str = Field(default="chat", description="chat | task | workflow")
    input: dict = Field(default_factory=dict, description="Execution input")
    output: dict = Field(default_factory=dict, description="Execution output")
    status: str = Field(..., description="success | failed | running")


router = APIRouter(prefix="/agent/runs", tags=["agent-runs"])


@router.post("", status_code=status.HTTP_201_CREATED)
def ingest_run(
    payload: AgentRunIngestRequest,
    db: Session = Depends(get_db_session),
) -> dict:
    """AgentRuntime 每次执行必须调用此接口写入日志。"""
    run = AgentRun(
        id=uuid.uuid4(),
        agent_id=uuid.UUID(payload.agent_id),
        type=(payload.type or "chat")[:32],
        input=payload.input or {},
        output=payload.output or {},
        status=(payload.status or "unknown")[:32],
    )
    repo = AgentRunRepository(db)
    repo.add(run)
    db.commit()
    return {"id": str(run.id), "agent_id": payload.agent_id, "status": run.status}
