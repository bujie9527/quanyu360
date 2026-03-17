"""Server CRUD, connectivity test, and environment setup endpoints."""
from __future__ import annotations

import socket
import threading
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
from app.schemas.server_schemas import ServerSetupResponse
from app.schemas.server_schemas import ServerTestResponse
from app.schemas.server_schemas import ServerUpdateRequest
from common.app.models import Server
from common.app.models import ServerSetupStatus
from common.app.models import ServerStatus

router = APIRouter(prefix="/admin/servers", tags=["servers"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
        setup_status=server.setup_status.value,
        setup_log=server.setup_log,
        created_at=server.created_at,
        updated_at=server.updated_at,
    )


def _run_setup_in_background(server_id: UUID, host: str, port: int, ssh_user: str, ssh_password: str | None) -> None:
    """Run server_setup.sh via SSH in a background thread and update DB on completion."""
    import paramiko  # imported here to avoid startup dependency if paramiko is missing

    # Read the setup script from the tools directory
    import os
    script_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", "..", "tools", "scripts", "server_setup.sh"
    )
    try:
        with open(script_path, "r") as f:
            setup_script = f.read()
    except FileNotFoundError:
        _update_setup_result(server_id, ServerSetupStatus.failed, "Setup script not found at tools/scripts/server_setup.sh")
        return

    log_lines: list[str] = []

    def _update_db(setup_status: ServerSetupStatus, log: str) -> None:
        from app.dependencies import SessionLocal
        with SessionLocal() as db:
            srv = db.get(Server, server_id)
            if srv:
                srv.setup_status = setup_status
                srv.setup_log = log
                if setup_status == ServerSetupStatus.completed:
                    srv.status = ServerStatus.active
                elif setup_status == ServerSetupStatus.failed:
                    srv.status = ServerStatus.inactive
                db.commit()

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port=port, username=ssh_user, password=ssh_password, timeout=30)

        # Run the setup script inline via bash
        stdin, stdout, stderr = client.exec_command(
            f"bash -s 2>&1", get_pty=True
        )
        stdin.write(setup_script)
        stdin.channel.shutdown_write()

        for line in stdout:
            log_lines.append(line.rstrip())
            # Update DB periodically for real-time log display
            if len(log_lines) % 10 == 0:
                _update_db(ServerSetupStatus.running, "\n".join(log_lines))

        exit_status = stdout.channel.recv_exit_status()
        client.close()

        full_log = "\n".join(log_lines)

        # Try to extract MySQL root password from script output
        mysql_root_pass = None
        for line in log_lines:
            if line.startswith("MYSQL_ROOT_PASSWORD="):
                mysql_root_pass = line.split("=", 1)[1].strip()

        if exit_status == 0:
            # Update MySQL credentials if found in setup output
            from app.dependencies import SessionLocal
            with SessionLocal() as db:
                srv = db.get(Server, server_id)
                if srv:
                    srv.setup_status = ServerSetupStatus.completed
                    srv.setup_log = full_log
                    srv.status = ServerStatus.active
                    if mysql_root_pass:
                        srv.mysql_admin_user = "root"
                        srv.mysql_admin_password = mysql_root_pass
                    db.commit()
        else:
            _update_db(ServerSetupStatus.failed, full_log)

    except Exception as exc:
        _update_db(ServerSetupStatus.failed, f"SSH error: {exc}\n" + "\n".join(log_lines))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("", response_model=ServerListResponse)
def list_servers(
    status: str | None = Query(default=None, pattern="^(active|inactive|pending_setup)$"),
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
        setup_status=ServerSetupStatus.pending,
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
    nullable_fields = {"ssh_password", "ssh_private_key", "mysql_admin_user", "mysql_admin_password"}
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
        return ServerTestResponse(success=True, message=f"SSH 端口 {server.host}:{server.port} 连通")
    except OSError as exc:
        return ServerTestResponse(success=False, message=f"连通性测试失败: {exc}")


@router.post("/{server_id}/setup", response_model=ServerSetupResponse)
def trigger_server_setup(server_id: UUID, db: Session = Depends(get_db_session)) -> ServerSetupResponse:
    """Trigger async environment setup (LEMP + WP-CLI) on the server via SSH."""
    server = db.get(Server, server_id)
    if server is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    if not server.ssh_password and not server.ssh_private_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SSH credentials not configured")
    if server.setup_status == ServerSetupStatus.running:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Setup already running")

    # Mark as running immediately
    server.setup_status = ServerSetupStatus.running
    server.setup_log = "Starting environment setup...\n"
    db.commit()

    # Run setup in background thread (non-blocking)
    t = threading.Thread(
        target=_run_setup_in_background,
        args=(server.id, server.host, server.port, server.ssh_user, server.ssh_password),
        daemon=True,
    )
    t.start()

    return ServerSetupResponse(
        success=True,
        message="Environment setup started. Check setup_log for progress.",
        setup_log="",
    )


@router.get("/{server_id}/setup-log", response_model=ServerSetupResponse)
def get_setup_log(server_id: UUID, db: Session = Depends(get_db_session)) -> ServerSetupResponse:
    """Poll for setup progress log."""
    server = db.get(Server, server_id)
    if server is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    return ServerSetupResponse(
        success=server.setup_status == ServerSetupStatus.completed,
        message=server.setup_status.value,
        setup_log=server.setup_log or "",
    )
