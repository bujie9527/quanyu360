"""Admin dashboard and list endpoints."""
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status

from app.dependencies import get_db_session
from app.repositories.admin_repository import AdminRepository
from app.schemas.dashboard_schemas import DashboardResponse
from app.services.dashboard_service import get_dashboard
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_admin_dashboard(db: Session = Depends(get_db_session)) -> DashboardResponse:
    data = get_dashboard(auth_session=db)
    return DashboardResponse(**data)


@router.get("/users")
def list_admin_users(
    tenant_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
):
    repo = AdminRepository(db)
    items, total = repo.list_users(tenant_id=tenant_id, limit=limit, offset=offset)
    return {"items": items, "total": total}


@router.get("/users/{user_id}")
def get_admin_user(
    user_id: UUID,
    db: Session = Depends(get_db_session),
):
    repo = AdminRepository(db)
    user = repo.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/projects")
def list_admin_projects(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
):
    repo = AdminRepository(db)
    items, total = repo.list_projects(limit=limit, offset=offset)
    return {"items": items, "total": total}


@router.get("/agents")
def list_admin_agents(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
):
    repo = AdminRepository(db)
    items, total = repo.list_agents(limit=limit, offset=offset)
    return {"items": items, "total": total}


@router.get("/tasks")
def list_admin_tasks(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
):
    repo = AdminRepository(db)
    items, total = repo.list_tasks(limit=limit, offset=offset)
    return {"items": items, "total": total}


@router.get("/workflows")
def list_admin_workflows(
    project_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
):
    repo = AdminRepository(db)
    items, total = repo.list_workflows(project_id=project_id, limit=limit, offset=offset)
    return {"items": items, "total": total}
