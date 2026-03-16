"""TaskRun/StepRun HTTP endpoints for Execution Log."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status

from pydantic import BaseModel
from pydantic import Field
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.dependencies import get_tenant_id_or_none
from app.repositories import TaskRunRepository


router = APIRouter(prefix="/task_runs", tags=["task-runs"])


class StepRunAppendRequest(BaseModel):
    step_name: str = Field(min_length=1, max_length=120)
    status: str = Field(min_length=1, max_length=32)
    duration: float = Field(ge=0)
    output_json: dict = Field(default_factory=dict)


class TaskRunStatusUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=32)
    end_time: str | None = None


@router.get("")
def list_task_runs(
    task_template_id: UUID | None = Query(default=None),
    workflow_id: UUID | None = Query(default=None),
    project_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
    tenant_id: UUID | None = Depends(get_tenant_id_or_none),
) -> dict:
    """List TaskRuns (execution logs). Filtered by tenant when tenant context present."""
    tid = tenant_id
    repo = TaskRunRepository(db)
    items, total = repo.list(
        task_template_id=task_template_id,
        workflow_id=workflow_id,
        project_id=project_id,
        tenant_id=tid,
        status=status,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [
            {
                "id": str(t.id),
                "task_template_id": str(t.task_template_id) if t.task_template_id else None,
                "workflow_id": str(t.workflow_id),
                "execution_id": t.execution_id,
                "status": t.status,
                "start_time": t.start_time.isoformat() if t.start_time else None,
                "end_time": t.end_time.isoformat() if t.end_time else None,
            }
            for t in items
        ],
        "total": total,
    }


@router.get("/{task_run_id}")
def get_task_run(
    task_run_id: UUID,
    db: Session = Depends(get_db_session),
    tenant_id: UUID | None = Depends(get_tenant_id_or_none),
) -> dict:
    """Get TaskRun with StepRuns. When tenant context present, verifies tenant ownership."""
    tid = tenant_id
    repo = TaskRunRepository(db)
    if tid is not None:
        tr = repo.get_by_tenant(task_run_id, tid)
    else:
        tr = repo.get(task_run_id)
    if tr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TaskRun not found")
    return {
        "id": str(tr.id),
        "task_template_id": str(tr.task_template_id) if tr.task_template_id else None,
        "workflow_id": str(tr.workflow_id),
        "execution_id": tr.execution_id,
        "status": tr.status,
        "start_time": tr.start_time.isoformat() if tr.start_time else None,
        "end_time": tr.end_time.isoformat() if tr.end_time else None,
        "step_runs": [
            {
                "id": str(sr.id),
                "step_name": sr.step_name,
                "status": sr.status,
                "duration": sr.duration,
                "output_json": sr.output_json,
            }
            for sr in tr.step_runs
        ],
    }


@router.post("/{task_run_id}/steps", status_code=status.HTTP_201_CREATED)
def append_step(
    task_run_id: UUID,
    payload: StepRunAppendRequest,
    db: Session = Depends(get_db_session),
) -> dict:
    """Append a StepRun. Called by workflow-engine after each step."""
    repo = TaskRunRepository(db)
    sr = repo.append_step(
        task_run_id=task_run_id,
        step_name=payload.step_name,
        status=payload.status,
        duration=payload.duration,
        output_json=payload.output_json,
    )
    db.commit()
    if sr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TaskRun not found")
    return {"id": str(sr.id), "step_name": sr.step_name, "status": sr.status}


@router.patch("/{task_run_id}")
def update_task_run_status(
    task_run_id: UUID,
    payload: TaskRunStatusUpdate,
    db: Session = Depends(get_db_session),
) -> dict:
    """Update TaskRun status/end_time. Called by workflow-engine on completion."""
    from datetime import datetime, timezone
    repo = TaskRunRepository(db)
    end_time = None
    if payload.end_time:
        try:
            end_time = datetime.fromisoformat(payload.end_time.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            end_time = datetime.now(timezone.utc)
    tr = repo.update_status(task_run_id, payload.status, end_time)
    db.commit()
    if tr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TaskRun not found")
    return {"id": str(tr.id), "status": tr.status}
