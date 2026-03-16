"""Server CRUD and connectivity test endpoints."""
from __future__ import annotations

import socket
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.schemas.server_schemas import ServerCreateRequest
from app.schemas.server_schemas import ServerListResponse
from app.schemas.server_schemas import ServerResponse
from app.schemas.server_schemas import ServerTestResponse
from app.schemas.server_schemas import ServerUpdateRequest
from common.app.models import Server
from common.app.models import ServerStatus

router = APIRouter(prefix="/admin/servers", tags=["servers"])


def _to_response(server: Server) -> ServerResponse:
    return ServerResponse(
        id=server.id,
        name=server.name,
        host=server.host,
        port=server.port,
        ssh_user=server.ssh_user,
        web_root=server.web_root,
        php_bin=server.php_bin,
        wp_cli_bin=server.wp_cli_bin,
        mysql_host=server.mysql_host,
        mysql_port=server.mysql_port,
        mysql_admin_user=server.mysql_admin_user,
        mysql_db_prefix=server.mysql_db_prefix,
        status=server.status.value,
        created_at=server.created_at,
        updated_at=server.updated_at,
    )


@router.get("", response_model=ServerListResponse)
def list_servers(
    status: str | None = Query(default=None, pattern="^(active|inactive)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> ServerListResponse:
    stmt = select(Server).order_by(Server.created_at.desc()).offset(offset).limit(limit)
    if status:
        stmt = stmt.where(Server.status == ServerStatus(status))
    items = list(db.scalars(stmt).all())

    count_stmt = select(func.count(Server.id))
    if status:
        count_stmt = count_stmt.where(Server.status == ServerStatus(status))
    total = db.scalar(count_stmt) or 0
    return ServerListResponse(items=[_to_response(item) for item in items], total=total)


@router.post("", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
def create_server(payload: ServerCreateRequest, db: Session = Depends(get_db_session)) -> ServerResponse:
    server = Server(
        name=payload.name,
        host=payload.host,
        port=payload.port,
        ssh_user=payload.ssh_user,
        ssh_password=payload.ssh_password,
        ssh_private_key=payload.ssh_private_key,
        web_root=payload.web_root,
        php_bin=payload.php_bin,
        wp_cli_bin=payload.wp_cli_bin,
        mysql_host=payload.mysql_host,
        mysql_port=payload.mysql_port,
        mysql_admin_user=payload.mysql_admin_user,
        mysql_admin_password=payload.mysql_admin_password,
        mysql_db_prefix=payload.mysql_db_prefix,
        status=ServerStatus(payload.status),
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    return _to_response(server)


@router.put("/{server_id}", response_model=ServerResponse)
def update_server(
    server_id: UUID,
    payload: ServerUpdateRequest,
    db: Session = Depends(get_db_session),
) -> ServerResponse:
    server = db.get(Server, server_id)
    if server is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    nullable_fields = {"ssh_password", "ssh_private_key"}
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if key == "status" and value is not None:
            setattr(server, key, ServerStatus(value))
        elif key in nullable_fields:
            setattr(server, key, value)
        elif value is not None:
            setattr(server, key, value)
    db.commit()
    db.refresh(server)
    return _to_response(server)


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_server(server_id: UUID, db: Session = Depends(get_db_session)) -> None:
    server = db.get(Server, server_id)
    if server is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    db.delete(server)
    db.commit()


@router.post("/{server_id}/test", response_model=ServerTestResponse)
def test_server_connectivity(server_id: UUID, db: Session = Depends(get_db_session)) -> ServerTestResponse:
    server = db.get(Server, server_id)
    if server is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    try:
        with socket.create_connection((server.host, server.port), timeout=5):
            pass
        return ServerTestResponse(success=True, message="SSH 端口连通")
    except OSError as exc:
        return ServerTestResponse(success=False, message=f"连通性测试失败: {exc}")
