"""Server management schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class ServerCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(default=22, ge=1, le=65535)
    ssh_user: str = Field(min_length=1, max_length=120)
    ssh_password: str | None = Field(default=None, max_length=255)
    ssh_private_key: str | None = None
    web_root: str = Field(min_length=1, max_length=512)
    php_bin: str = Field(default="php", max_length=255)
    wp_cli_bin: str = Field(default="wp", max_length=255)
    mysql_host: str = Field(default="localhost", max_length=255)
    mysql_port: int = Field(default=3306, ge=1, le=65535)
    mysql_admin_user: str = Field(min_length=1, max_length=120)
    mysql_admin_password: str = Field(min_length=1, max_length=255)
    mysql_db_prefix: str = Field(default="wp_", max_length=32)
    status: str = Field(default="active", pattern="^(active|inactive)$")


class ServerUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    host: str | None = Field(default=None, min_length=1, max_length=255)
    port: int | None = Field(default=None, ge=1, le=65535)
    ssh_user: str | None = Field(default=None, min_length=1, max_length=120)
    ssh_password: str | None = Field(default=None, max_length=255)
    ssh_private_key: str | None = None
    web_root: str | None = Field(default=None, min_length=1, max_length=512)
    php_bin: str | None = Field(default=None, max_length=255)
    wp_cli_bin: str | None = Field(default=None, max_length=255)
    mysql_host: str | None = Field(default=None, max_length=255)
    mysql_port: int | None = Field(default=None, ge=1, le=65535)
    mysql_admin_user: str | None = Field(default=None, min_length=1, max_length=120)
    mysql_admin_password: str | None = Field(default=None, min_length=1, max_length=255)
    mysql_db_prefix: str | None = Field(default=None, max_length=32)
    status: str | None = Field(default=None, pattern="^(active|inactive)$")


class ServerResponse(BaseModel):
    id: UUID
    name: str
    host: str
    port: int
    ssh_user: str
    web_root: str
    php_bin: str
    wp_cli_bin: str
    mysql_host: str
    mysql_port: int
    mysql_admin_user: str
    mysql_db_prefix: str
    status: str
    created_at: datetime
    updated_at: datetime


class ServerListResponse(BaseModel):
    items: list[ServerResponse]
    total: int


class ServerTestResponse(BaseModel):
    success: bool
    message: str
