"""add project team members

Revision ID: 20260308_0002
Revises: 20260308_0001
Create Date: 2026-03-08 15:05:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260308_0002"
down_revision = "20260308_0001"
branch_labels = None
depends_on = None


user_role = postgresql.ENUM("admin", "manager", "operator", name="user_role", create_type=False)


def upgrade() -> None:
    op.create_table(
        "project_team_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", user_role, server_default="operator", nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_project_team_members_project_id_projects",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_project_team_members_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_project_team_members"),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_team_members_project_id_user_id"),
        if_not_exists=True,
    )
    op.create_index("ix_project_team_members_project_id", "project_team_members", ["project_id"], unique=False, if_not_exists=True)
    op.create_index("ix_project_team_members_user_id", "project_team_members", ["user_id"], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_project_team_members_user_id", table_name="project_team_members")
    op.drop_index("ix_project_team_members_project_id", table_name="project_team_members")
    op.drop_table("project_team_members")
