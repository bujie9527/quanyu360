"""Admin cross-DB / cross-service data access."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

import httpx

from app.config import settings
from common.app.models import User


class AdminRepository:
    """Fetches admin data from auth_db and proxies to other services."""

    def __init__(self, db: Session):
        self.db = db

    def list_users(
        self,
        tenant_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        statement = select(User).options()
        count_stmt = select(func.count(User.id))
        if tenant_id is not None:
            statement = statement.where(User.tenant_id == tenant_id)
            count_stmt = count_stmt.where(User.tenant_id == tenant_id)
        items = list(self.db.scalars(statement.order_by(User.created_at.desc()).offset(offset).limit(limit)).all())
        total = self.db.scalar(count_stmt) or 0
        return [
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "tenant_id": str(u.tenant_id),
                "role": u.role.value if hasattr(u.role, "value") else str(u.role),
                "status": u.status.value if hasattr(u.status, "value") else str(u.status),
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in items
        ], total

    def _fetch_from_service(self, base_url: str, path: str, params: dict | None = None) -> dict:
        try:
            url = f"{base_url.rstrip('/')}{path}"
            with httpx.Client(timeout=10.0) as client:
                r = client.get(url, params=params or {})
                r.raise_for_status()
                return r.json()
        except Exception:
            return {"items": [], "total": 0}

    def list_projects(self, limit: int = 50, offset: int = 0) -> tuple[list[dict], int]:
        data = self._fetch_from_service(
            settings.project_service_url,
            "/projects",
            {"limit": limit, "offset": offset},
        )
        return data.get("items", []), data.get("total", 0)

    def list_agents(self, limit: int = 50, offset: int = 0) -> tuple[list[dict], int]:
        data = self._fetch_from_service(
            settings.agent_service_url,
            "/agents",
            {"limit": limit, "offset": offset},
        )
        return data.get("items", []), data.get("total", 0)

    def list_tasks(self, limit: int = 50, offset: int = 0) -> tuple[list[dict], int]:
        data = self._fetch_from_service(
            settings.task_service_url,
            "/tasks",
            {"limit": limit, "offset": offset},
        )
        return data.get("items", []), data.get("total", 0)

    def list_workflows(
        self,
        project_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        params: dict = {"limit": limit, "offset": offset}
        if project_id is not None:
            params["project_id"] = str(project_id)
        data = self._fetch_from_service(
            settings.workflow_service_url,
            "/workflows",
            params,
        )
        return data.get("items", []), data.get("total", 0)

    def get_user(self, user_id: UUID) -> dict | None:
        user = self.db.get(User, user_id)
        if user is None:
            return None
        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "tenant_id": str(user.tenant_id),
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "status": user.status.value if hasattr(user.status, "value") else str(user.status),
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        }
