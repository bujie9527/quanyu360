"""AgentRun data access."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from common.app.models import AgentRun


class AgentRunRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, run: AgentRun) -> None:
        self.db.add(run)
        self.db.flush()
