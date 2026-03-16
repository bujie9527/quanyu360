"""update task execution fields

Revision ID: 20260308_0004
Revises: 20260308_0003
Create Date: 2026-03-08 16:05:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260308_0004"
down_revision = "20260308_0003"
branch_labels = None
depends_on = None


old_task_status = sa.Enum(
    "queued",
    "in_progress",
    "blocked",
    "waiting_review",
    "completed",
    "failed",
    "cancelled",
    name="task_status",
)

new_task_status = sa.Enum(
    "pending",
    "running",
    "completed",
    "failed",
    "cancelled",
    name="task_status_new",
)


def _task_status_already_migrated(conn) -> bool:
    """Check if task_status already has new values (pending, running)."""
    r = conn.execute(sa.text("""
        SELECT enumlabel FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname = 'task_status'
    """)).fetchall()
    labels = [row[0] for row in r]
    return "pending" in labels or "running" in labels


def upgrade() -> None:
    conn = op.get_bind()
    new_task_status.create(conn, checkfirst=True)

    if not _task_status_already_migrated(conn):
        op.execute("ALTER TABLE tasks ALTER COLUMN status DROP DEFAULT")
        op.execute(
            """
            ALTER TABLE tasks
            ALTER COLUMN status TYPE task_status_new
            USING (
              CASE status::text
                WHEN 'queued' THEN 'pending'
                WHEN 'in_progress' THEN 'running'
                WHEN 'blocked' THEN 'running'
                WHEN 'waiting_review' THEN 'running'
                WHEN 'completed' THEN 'completed'
                WHEN 'failed' THEN 'failed'
                WHEN 'cancelled' THEN 'cancelled'
              END
            )::task_status_new
            """
        )
        op.execute("DROP TYPE task_status")
        op.execute("ALTER TYPE task_status_new RENAME TO task_status")
        op.alter_column("tasks", "status", server_default="pending")

    # Add columns if not exist
    from sqlalchemy import inspect
    insp = inspect(conn)
    cols = {c["name"] for c in insp.get_columns("tasks")}
    if "attempt_count" not in cols:
        op.add_column("tasks", sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False))
    if "max_attempts" not in cols:
        op.add_column("tasks", sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False))
    if "last_error" not in cols:
        op.add_column("tasks", sa.Column("last_error", sa.Text(), nullable=True))


def downgrade() -> None:
    reverted_task_status = sa.Enum(
        "queued",
        "in_progress",
        "blocked",
        "waiting_review",
        "completed",
        "failed",
        "cancelled",
        name="task_status_old",
    )
    bind = op.get_bind()
    reverted_task_status.create(bind, checkfirst=True)

    op.execute(
        """
        ALTER TABLE tasks
        ALTER COLUMN status TYPE task_status_old
        USING (
          CASE status::text
            WHEN 'pending' THEN 'queued'
            WHEN 'running' THEN 'in_progress'
            WHEN 'completed' THEN 'completed'
            WHEN 'failed' THEN 'failed'
            WHEN 'cancelled' THEN 'cancelled'
          END
        )::task_status_old
        """
    )

    op.execute("DROP TYPE task_status")
    op.execute("ALTER TYPE task_status_old RENAME TO task_status")

    op.drop_column("tasks", "last_error")
    op.drop_column("tasks", "max_attempts")
    op.drop_column("tasks", "attempt_count")
    op.alter_column("tasks", "status", server_default="queued")
