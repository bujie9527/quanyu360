"""Schedule business logic: schedule -> task_template -> workflow."""
from __future__ import annotations

import logging
from datetime import datetime
from datetime import timezone
from uuid import UUID

from fastapi import HTTPException
from fastapi import status

from app.repositories import ScheduleRepository
from app.repositories import TaskTemplateRepository
from app.schemas.schedule_schemas import ScheduleCreateRequest
from app.schemas.schedule_schemas import ScheduleUpdateRequest
from app.schemas.workflow_schemas import WorkflowExecutionRequest
from common.app.models import Schedule
from common.app.models import TaskTemplate

logger = logging.getLogger(__name__)


class ScheduleService:
    def __init__(
        self,
        schedule_repo: ScheduleRepository,
        task_template_repo: TaskTemplateRepository,
        workflow_executor: callable,
    ):
        self.schedule_repo = schedule_repo
        self.task_template_repo = task_template_repo
        self._execute_workflow = workflow_executor

    def list(
        self,
        task_template_id: UUID | None = None,
        enabled: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Schedule], int]:
        return self.schedule_repo.list(
            task_template_id=task_template_id,
            enabled=enabled,
            limit=limit,
            offset=offset,
        )

    def get(self, schedule_id: UUID) -> Schedule:
        s = self.schedule_repo.get(schedule_id)
        if s is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
        return s

    def create(self, payload: ScheduleCreateRequest) -> Schedule:
        tpl = self.task_template_repo.get(payload.task_template_id)
        if tpl is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TaskTemplate not found")
        if tpl.workflow_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TaskTemplate must have workflow_id",
            )
        schedule = Schedule(
            task_template_id=payload.task_template_id,
            cron=payload.cron,
            target_sites=payload.target_sites or [],
            enabled=payload.enabled,
        )
        self.schedule_repo.add(schedule)
        self.schedule_repo.db.commit()
        self.schedule_repo.db.refresh(schedule)
        return schedule

    def update(self, schedule_id: UUID, payload: ScheduleUpdateRequest) -> Schedule:
        s = self.get(schedule_id)
        if payload.cron is not None:
            s.cron = payload.cron
        if payload.target_sites is not None:
            s.target_sites = payload.target_sites
        if payload.enabled is not None:
            s.enabled = payload.enabled
        self.schedule_repo.db.commit()
        self.schedule_repo.db.refresh(s)
        return s

    def delete(self, schedule_id: UUID) -> None:
        s = self.get(schedule_id)
        self.schedule_repo.delete(s)
        self.schedule_repo.db.commit()

    def trigger(self, schedule_id: UUID) -> list[dict]:
        """Execute schedule: task_template -> workflow with target_sites."""
        s = self.get(schedule_id)
        tpl = self.task_template_repo.get(s.task_template_id)
        if tpl is None or tpl.workflow_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TaskTemplate or workflow not found",
            )
        results = []
        base_payload = {
            "trigger": "schedule",
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "schedule_id": str(s.id),
            "target_sites": s.target_sites,
            "task_template_id": str(tpl.id),
        }

        if s.target_sites:
            for site_id in s.target_sites:
                inp = {**base_payload, "site_id": site_id}
                try:
                    r = self._execute_workflow(tpl.workflow_id, WorkflowExecutionRequest(input_payload=inp))
                    results.append({"site_id": site_id, "ok": True, "execution": r})
                except Exception as e:
                    logger.warning("Schedule %s site %s failed: %s", s.id, site_id, e)
                    results.append({"site_id": site_id, "ok": False, "error": str(e)})
        else:
            try:
                r = self._execute_workflow(tpl.workflow_id, WorkflowExecutionRequest(input_payload=base_payload))
                results.append({"ok": True, "execution": r})
            except Exception as e:
                logger.warning("Schedule %s failed: %s", s.id, e)
                results.append({"ok": False, "error": str(e)})
        return results

    def tick(self) -> list[dict]:
        """Check due schedules and trigger each. Called by scheduler."""
        now = datetime.now(timezone.utc)
        due = self.schedule_repo.list_due(now)
        all_results = []
        for s in due:
            try:
                results = self.trigger(s.id)
                all_results.extend([{"schedule_id": str(s.id), **r} for r in results])
            except Exception as e:
                logger.warning("Schedule tick %s failed: %s", s.id, e)
                all_results.append({"schedule_id": str(s.id), "ok": False, "error": str(e)})
        return all_results
