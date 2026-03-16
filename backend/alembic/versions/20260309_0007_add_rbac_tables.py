"""add RBAC tables (roles, permissions, role_permissions, user_role_assignments)

Revision ID: 20260309_0007
Revises: 20260309_0006
Create Date: 2026-03-09

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260309_0007"
down_revision = "20260309_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_roles_slug"),
        if_not_exists=True,
    )
    op.create_index("ix_roles_slug", "roles", ["slug"], unique=True, if_not_exists=True)

    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("resource", sa.String(80), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_permissions_slug"),
        if_not_exists=True,
    )
    op.create_index("ix_permissions_slug", "permissions", ["slug"], unique=True, if_not_exists=True)

    op.create_table(
        "role_permissions",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_permission"),
        if_not_exists=True,
    )

    op.create_table(
        "user_role_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.create_index("ix_user_role_assignments_user", "user_role_assignments", ["user_id"], if_not_exists=True)
    op.create_index("ix_user_role_assignments_tenant", "user_role_assignments", ["tenant_id"], if_not_exists=True)
    # Prevent duplicate (user, role) for platform scope (tenant_id IS NULL)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_user_role_platform ON user_role_assignments (user_id, role_id) WHERE tenant_id IS NULL"
    )
    # Prevent duplicate (user, role, tenant) for tenant scope
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_user_role_tenant ON user_role_assignments (user_id, role_id, tenant_id) WHERE tenant_id IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_index("uq_user_role_tenant", table_name="user_role_assignments")
    op.drop_index("uq_user_role_platform", table_name="user_role_assignments")
    op.drop_index("ix_user_role_assignments_tenant", table_name="user_role_assignments")
    op.drop_index("ix_user_role_assignments_user", table_name="user_role_assignments")
    op.drop_table("user_role_assignments")
    op.drop_table("role_permissions")
    op.drop_index("ix_permissions_slug", table_name="permissions")
    op.drop_table("permissions")
    op.drop_index("ix_roles_slug", table_name="roles")
    op.drop_table("roles")
