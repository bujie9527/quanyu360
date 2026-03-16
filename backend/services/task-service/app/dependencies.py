from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from app.config import session_factory
from app.repositories import TaskRepository
from app.services import TaskService
from common.app.db.session import get_db


def get_db_session() -> Generator[Session, None, None]:
    if session_factory is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session factory is not configured.",
        )
    yield from get_db(session_factory)


def get_task_service(db: Session = Depends(get_db_session)) -> TaskService:
    return TaskService(TaskRepository(db))
