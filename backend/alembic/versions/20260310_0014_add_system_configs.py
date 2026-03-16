"""add system_configs table for admin system configuration

Revision ID: 20260310_0014
Revises: 20260310_0013
Create Date: 2026-03-10

"""
from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260310_0014"
down_revision = "20260310_0013"
branch_labels = None
depends_on = None


DEFAULT_KEYS = [
    ("OPENAI_API_KEY", "", "llm", True, "OpenAI API key for GPT models"),
    ("OPENAI_BASE_URL", "https://api.openai.com/v1", "llm", False, "OpenAI API base URL"),
    ("CLAUDE_API_KEY", "", "llm", True, "Anthropic Claude API key"),
    ("CLAUDE_BASE_URL", "https://api.anthropic.com/v1", "llm", False, "Claude API base URL"),
    ("LOCAL_MODEL_BASE_URL", "http://localhost:11434/v1", "llm", False, "Local model (Ollama) base URL"),
    ("LOCAL_MODEL_API_KEY", "", "llm", True, "Local model API key if required"),
    ("QDRANT_URL", "http://qdrant:6333", "general", False, "Qdrant vector DB URL for embeddings"),
    ("LLM_REQUEST_TIMEOUT_SECONDS", "30", "llm", False, "LLM request timeout in seconds"),
]

def upgrade() -> None:
    op.create_table(
        "system_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=60), nullable=False),
        sa.Column("is_secret", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", name="uq_system_configs_key"),
        if_not_exists=True,
    )
    op.create_index("ix_system_configs_category", "system_configs", ["category"], unique=False, if_not_exists=True)

    # Seed default keys
    conn = op.get_bind()
    for key, value, category, is_secret, description in DEFAULT_KEYS:
        rid = str(uuid.uuid4())
        conn.execute(
            sa.text(
                "INSERT INTO system_configs (id, created_at, updated_at, key, value, category, is_secret, description) "
                "VALUES (:id, now(), now(), :key, :value, :category, :is_secret, :description) "
                "ON CONFLICT (key) DO NOTHING"
            ),
            {
                "id": rid,
                "key": key,
                "value": value,
                "category": category,
                "is_secret": is_secret,
                "description": description,
            },
        )


def downgrade() -> None:
    op.drop_index("ix_system_configs_category", table_name="system_configs")
    op.drop_table("system_configs")
