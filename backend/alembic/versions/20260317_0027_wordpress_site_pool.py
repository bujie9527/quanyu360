"""allow wordpress site pool and install tracking

Revision ID: 20260317_0027
Revises: 20260316_0026
Create Date: 2026-03-17
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260317_0027"
down_revision = "20260316_0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("wordpress_sites", sa.Column("server_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("wordpress_sites", sa.Column("install_task_run_id", postgresql.UUID(as_uuid=True), nullable=True))

    op.create_index("ix_wordpress_sites_server_id", "wordpress_sites", ["server_id"], unique=False)
    op.create_index("ix_wordpress_sites_install_task_run_id", "wordpress_sites", ["install_task_run_id"], unique=False)

    op.create_foreign_key(
        "fk_wordpress_sites_server_id",
        "wordpress_sites",
        "servers",
        ["server_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_wordpress_sites_install_task_run_id",
        "wordpress_sites",
        "task_runs",
        ["install_task_run_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.alter_column("wordpress_sites", "tenant_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)
    op.alter_column("wordpress_sites", "project_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)


def downgrade() -> None:
    op.alter_column("wordpress_sites", "project_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
    op.alter_column("wordpress_sites", "tenant_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)

    op.drop_constraint("fk_wordpress_sites_install_task_run_id", "wordpress_sites", type_="foreignkey")
    op.drop_constraint("fk_wordpress_sites_server_id", "wordpress_sites", type_="foreignkey")

    op.drop_index("ix_wordpress_sites_install_task_run_id", table_name="wordpress_sites")
    op.drop_index("ix_wordpress_sites_server_id", table_name="wordpress_sites")

    op.drop_column("wordpress_sites", "install_task_run_id")
    op.drop_column("wordpress_sites", "server_id")
