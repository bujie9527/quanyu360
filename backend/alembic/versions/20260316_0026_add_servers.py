"""add servers table and platform_domain.server_id

Revision ID: 20260316_0026
Revises: 20260316_0025
Create Date: 2026-03-16
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260316_0026"
down_revision = "20260316_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    server_status_enum = sa.Enum("active", "inactive", name="server_status")
    bind = op.get_bind()
    server_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "servers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("host", sa.String(length=255), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False, server_default="22"),
        sa.Column("ssh_user", sa.String(length=120), nullable=False),
        sa.Column("ssh_password", sa.String(length=255), nullable=True),
        sa.Column("ssh_private_key", sa.Text(), nullable=True),
        sa.Column("web_root", sa.String(length=512), nullable=False),
        sa.Column("php_bin", sa.String(length=255), nullable=False, server_default="php"),
        sa.Column("wp_cli_bin", sa.String(length=255), nullable=False, server_default="wp"),
        sa.Column("mysql_host", sa.String(length=255), nullable=False, server_default="localhost"),
        sa.Column("mysql_port", sa.Integer(), nullable=False, server_default="3306"),
        sa.Column("mysql_admin_user", sa.String(length=120), nullable=False),
        sa.Column("mysql_admin_password", sa.String(length=255), nullable=False),
        sa.Column("mysql_db_prefix", sa.String(length=32), nullable=False, server_default="wp_"),
        sa.Column("status", server_status_enum, nullable=False, server_default="active"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_servers_name"),
    )
    op.create_index("ix_servers_status", "servers", ["status"], unique=False)
    op.create_index("ix_servers_host_port", "servers", ["host", "port"], unique=False)

    op.add_column("platform_domains", sa.Column("server_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_platform_domains_server_id", "platform_domains", ["server_id"], unique=False)
    op.create_foreign_key(
        "fk_platform_domains_server_id",
        "platform_domains",
        "servers",
        ["server_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_platform_domains_server_id", "platform_domains", type_="foreignkey")
    op.drop_index("ix_platform_domains_server_id", table_name="platform_domains")
    op.drop_column("platform_domains", "server_id")

    op.drop_index("ix_servers_host_port", table_name="servers")
    op.drop_index("ix_servers_status", table_name="servers")
    op.drop_table("servers")

    bind = op.get_bind()
    sa.Enum(name="server_status").drop(bind, checkfirst=True)
