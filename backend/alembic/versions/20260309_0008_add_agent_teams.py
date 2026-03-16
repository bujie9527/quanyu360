"""add agent_teams and agent_team_members tables, team_id on tasks

Revision ID: 20260309_0008
Revises: 20260309_0007
Create Date: 2026-03-09

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260309_0008"
down_revision = "20260309_0007"
branch_labels = None
depends_on = None


def _create_enum_if_not_exists(name: str, values: list[str]) -> str:
    vals = ", ".join(f"'{v}'" for v in values)
    return f"""
    DO $$ BEGIN
        CREATE TYPE {name} AS ENUM ({vals});
    EXCEPTION WHEN duplicate_object THEN NULL;
    END $$;
    """


def upgrade() -> None:
    op.execute(_create_enum_if_not_exists("team_execution_type", ["sequential", "parallel", "review_loop"]))
    team_execution_type = postgresql.ENUM(
        "sequential",
        "parallel",
        "review_loop",
        name="team_execution_type",
        create_type=False,
    )

    op.create_table(
        "agent_teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "execution_type",
            team_execution_type,
            nullable=False,
            server_default="sequential",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_agent_teams_project_id_projects", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "slug", name="uq_agent_teams_project_id_slug"),
        if_not_exists=True,
    )
    op.create_index("ix_agent_teams_project_execution", "agent_teams", ["project_id", "execution_type"], unique=False, if_not_exists=True)

    op.create_table(
        "agent_team_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("role_in_team", sa.String(120), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], name="fk_agent_team_members_agent_id_agents", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["agent_teams.id"], name="fk_agent_team_members_team_id_agent_teams", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "agent_id", name="uq_agent_team_members_team_id_agent_id"),
        if_not_exists=True,
    )
    op.create_index("ix_agent_team_members_agent_id", "agent_team_members", ["agent_id"], unique=False, if_not_exists=True)
    op.create_index("ix_agent_team_members_team_id", "agent_team_members", ["team_id"], unique=False, if_not_exists=True)

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = current_schema() AND table_name = 'tasks' AND column_name = 'team_id'
            ) THEN
                ALTER TABLE tasks ADD COLUMN team_id UUID;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_schema = current_schema() AND constraint_name = 'fk_tasks_team_id_agent_teams'
            ) THEN
                ALTER TABLE tasks ADD CONSTRAINT fk_tasks_team_id_agent_teams
                FOREIGN KEY (team_id) REFERENCES agent_teams(id) ON DELETE SET NULL;
            END IF;
        END $$;
    """)
    op.create_index("ix_tasks_team_id", "tasks", ["team_id"], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_tasks_team_id", table_name="tasks")
    op.drop_constraint("fk_tasks_team_id_agent_teams", "tasks", type_="foreignkey")
    op.drop_column("tasks", "team_id")

    op.drop_index("ix_agent_team_members_team_id", table_name="agent_team_members")
    op.drop_index("ix_agent_team_members_agent_id", table_name="agent_team_members")
    op.drop_table("agent_team_members")

    op.drop_index("ix_agent_teams_project_execution", table_name="agent_teams")
    op.drop_table("agent_teams")

    sa.Enum(name="team_execution_type").drop(op.get_bind(), checkfirst=True)
