"""Schedule data access."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from common.app.models import Schedule


class ScheduleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        task_template_id: UUID | None = None,
        enabled: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Schedule], int]:
        stmt = select(Schedule)
        count_stmt = select(func.count(Schedule.id))
        if task_template_id is not None:
            stmt = stmt.where(Schedule.task_template_id == task_template_id)
            count_stmt = count_stmt.where(Schedule.task_template_id == task_template_id)
        if enabled is not None:
            stmt = stmt.where(Schedule.enabled.is_(enabled))
            count_stmt = count_stmt.where(Schedule.enabled.is_(enabled))
        total = self.db.scalar(count_stmt) or 0
        items = list(
            self.db.scalars(stmt.order_by(Schedule.created_at.desc()).offset(offset).limit(limit))
        )
        return items, total

    def list_due(self, at: datetime) -> list[Schedule]:
        """Return enabled schedules whose cron matches the given time."""
        import croniter

        stmt = select(Schedule).where(Schedule.enabled.is_(True))
        all_schedules = list(self.db.scalars(stmt))
        due = []
        for s in all_schedules:
            if croniter.is_valid(s.cron) and croniter.match(s.cron, at):
                due.append(s)
        return due

    def get(self, schedule_id: UUID) -> Schedule | None:
        return self.db.get(Schedule, schedule_id)

    def add(self, schedule: Schedule) -> None:
        self.db.add(schedule)

    def delete(self, schedule: Schedule) -> None:
        self.db.delete(schedule)
