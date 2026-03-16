"""add webhook to workflow_trigger_type enum

Revision ID: 20260310_0010
Revises: 20260309_0009
Create Date: 2026-03-10

"""
from __future__ import annotations

from alembic import op

revision = "20260310_0010"
down_revision = "20260309_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE workflow_trigger_type ADD VALUE IF NOT EXISTS 'webhook'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values; requires recreate
    pass
