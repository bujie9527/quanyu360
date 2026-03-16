"""update workflow steps for engine

Revision ID: 20260308_0005
Revises: 20260308_0004
Create Date: 2026-03-08 16:35:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260308_0005"
down_revision = "20260308_0004"
branch_labels = None
depends_on = None


old_workflow_step_type = sa.Enum(
    "agent_task",
    "tool_call",
    "approval",
    "condition",
    "webhook",
    name="workflow_step_type",
)

new_workflow_step_type = sa.Enum(
    "agent_task",
    "tool_call",
    "condition",
    "delay",
    name="workflow_step_type_new",
)


def upgrade() -> None:
    bind = op.get_bind()
    new_workflow_step_type.create(bind, checkfirst=True)

    op.execute(
        """
        ALTER TABLE workflow_steps
        ALTER COLUMN step_type TYPE workflow_step_type_new
        USING (
          CASE step_type::text
            WHEN 'agent_task' THEN 'agent_task'
            WHEN 'tool_call' THEN 'tool_call'
            WHEN 'condition' THEN 'condition'
            WHEN 'approval' THEN 'condition'
            WHEN 'webhook' THEN 'tool_call'
          END
        )::workflow_step_type_new
        """
    )

    op.execute("DROP TYPE workflow_step_type")
    op.execute("ALTER TYPE workflow_step_type_new RENAME TO workflow_step_type")

    from sqlalchemy import inspect
    conn = op.get_bind()
    cols = {c["name"] for c in inspect(conn).get_columns("workflow_steps")}
    if "next_step_key" not in cols:
        op.add_column("workflow_steps", sa.Column("next_step_key", sa.String(length=120), nullable=True))


def downgrade() -> None:
    reverted_workflow_step_type = sa.Enum(
        "agent_task",
        "tool_call",
        "approval",
        "condition",
        "webhook",
        name="workflow_step_type_old",
    )
    bind = op.get_bind()
    reverted_workflow_step_type.create(bind, checkfirst=True)

    op.execute(
        """
        ALTER TABLE workflow_steps
        ALTER COLUMN step_type TYPE workflow_step_type_old
        USING (
          CASE step_type::text
            WHEN 'agent_task' THEN 'agent_task'
            WHEN 'tool_call' THEN 'tool_call'
            WHEN 'condition' THEN 'condition'
            WHEN 'delay' THEN 'condition'
          END
        )::workflow_step_type_old
        """
    )

    op.execute("DROP TYPE workflow_step_type")
    op.execute("ALTER TYPE workflow_step_type_old RENAME TO workflow_step_type")
    op.drop_column("workflow_steps", "next_step_key")
