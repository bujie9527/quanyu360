"""create platform schema

Revision ID: 20260308_0001
Revises:
Create Date: 2026-03-08 14:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260308_0001"
down_revision = None
branch_labels = None
depends_on = None


# 使用 postgresql.ENUM 并 create_type=False，避免 before_create 重复创建
tenant_status = postgresql.ENUM("active", "suspended", "archived", name="tenant_status", create_type=False)
user_role = postgresql.ENUM("admin", "manager", "operator", name="user_role", create_type=False)
user_status = postgresql.ENUM("invited", "active", "disabled", name="user_status", create_type=False)
project_status = postgresql.ENUM("draft", "active", "archived", name="project_status", create_type=False)
agent_status = postgresql.ENUM("draft", "active", "paused", "archived", name="agent_status", create_type=False)
task_priority = postgresql.ENUM("low", "normal", "high", "urgent", name="task_priority", create_type=False)
task_status = postgresql.ENUM(
    "queued",
    "in_progress",
    "blocked",
    "waiting_review",
    "completed",
    "failed",
    "cancelled",
    name="task_status",
    create_type=False,
)
workflow_status = postgresql.ENUM("draft", "active", "archived", name="workflow_status", create_type=False)
workflow_trigger_type = postgresql.ENUM("manual", "scheduled", "event", name="workflow_trigger_type", create_type=False)
workflow_step_type = postgresql.ENUM("agent_task", "tool_call", "approval", "condition", "webhook", name="workflow_step_type", create_type=False)
terminal_status = postgresql.ENUM("idle", "connected", "busy", "offline", "terminated", name="terminal_status", create_type=False)
tool_type = postgresql.ENUM("api", "terminal", "knowledge", "integration", name="tool_type", create_type=False)
audit_action = postgresql.ENUM("create", "update", "delete", "execute", "assign", "login", name="audit_action", create_type=False)


def _create_enum_if_not_exists(name: str, values: list[str]) -> str:
    vals = ", ".join(f"'{v}'" for v in values)
    return f"""
    DO $$ BEGIN
        CREATE TYPE {name} AS ENUM ({vals});
    EXCEPTION WHEN duplicate_object THEN NULL;
    END $$;
    """


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    op.execute(_create_enum_if_not_exists("tenant_status", ["active", "suspended", "archived"]))
    op.execute(_create_enum_if_not_exists("user_role", ["admin", "manager", "operator"]))
    op.execute(_create_enum_if_not_exists("user_status", ["invited", "active", "disabled"]))
    op.execute(_create_enum_if_not_exists("project_status", ["draft", "active", "archived"]))
    op.execute(_create_enum_if_not_exists("agent_status", ["draft", "active", "paused", "archived"]))
    op.execute(_create_enum_if_not_exists("task_priority", ["low", "normal", "high", "urgent"]))
    op.execute(_create_enum_if_not_exists("task_status", [
        "queued", "in_progress", "blocked", "waiting_review", "completed", "failed", "cancelled"
    ]))
    op.execute(_create_enum_if_not_exists("workflow_status", ["draft", "active", "archived"]))
    op.execute(_create_enum_if_not_exists("workflow_trigger_type", ["manual", "scheduled", "event"]))
    op.execute(_create_enum_if_not_exists("workflow_step_type", ["agent_task", "tool_call", "approval", "condition", "webhook"]))
    op.execute(_create_enum_if_not_exists("terminal_status", ["idle", "connected", "busy", "offline", "terminated"]))
    op.execute(_create_enum_if_not_exists("tool_type", ["api", "terminal", "knowledge", "integration"]))
    op.execute(_create_enum_if_not_exists("audit_action", ["create", "update", "delete", "execute", "assign", "login"]))

    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("status", tenant_status, server_default="active", nullable=False),
        sa.Column("plan_name", sa.String(length=80), server_default="mvp", nullable=False),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_tenants"),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
        if_not_exists=True,
    )
    op.create_index("ix_tenants_status", "tenants", ["status"], unique=False, if_not_exists=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, server_default="operator", nullable=False),
        sa.Column("status", user_status, server_default="invited", nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_users_tenant_id_tenants", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_id_email"),
        if_not_exists=True,
    )
    op.create_index("ix_users_tenant_status", "users", ["tenant_id", "status"], unique=False, if_not_exists=True)
    op.create_index("ix_users_tenant_role", "users", ["tenant_id", "role"], unique=False, if_not_exists=True)

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("key", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", project_status, server_default="draft", nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], name="fk_projects_owner_user_id_users", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_projects_tenant_id_tenants", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_projects"),
        sa.UniqueConstraint("tenant_id", "key", name="uq_projects_tenant_id_key"),
        if_not_exists=True,
    )
    op.create_index("ix_projects_tenant_status", "projects", ["tenant_id", "status"], unique=False, if_not_exists=True)
    op.create_index("ix_projects_owner_user_id", "projects", ["owner_user_id"], unique=False, if_not_exists=True)

    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("role_title", sa.String(length=120), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("status", agent_status, server_default="draft", nullable=False),
        sa.Column("max_concurrency", sa.Integer(), server_default="1", nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name="fk_agents_created_by_user_id_users", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_agents_project_id_projects", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_agents"),
        sa.UniqueConstraint("project_id", "slug", name="uq_agents_project_id_slug"),
        if_not_exists=True,
    )
    op.create_index("ix_agents_project_status", "agents", ["project_id", "status"], unique=False, if_not_exists=True)
    op.create_index("ix_agents_project_model", "agents", ["project_id", "model"], unique=False, if_not_exists=True)

    op.create_table(
        "tools",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("tool_type", tool_type, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_tools_project_id_projects", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_tools"),
        sa.UniqueConstraint("project_id", "slug", name="uq_tools_project_id_slug"),
        if_not_exists=True,
    )
    op.create_index("ix_tools_project_enabled", "tools", ["project_id", "is_enabled"], unique=False, if_not_exists=True)
    op.create_index("ix_tools_project_type", "tools", ["project_id", "tool_type"], unique=False, if_not_exists=True)

    op.create_table(
        "workflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("status", workflow_status, server_default="draft", nullable=False),
        sa.Column("trigger_type", workflow_trigger_type, server_default="manual", nullable=False),
        sa.Column("definition", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_workflows_project_id_projects", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_workflows"),
        sa.UniqueConstraint("project_id", "slug", "version", name="uq_workflows_project_id_slug_version"),
        if_not_exists=True,
    )
    op.create_index("ix_workflows_project_status", "workflows", ["project_id", "status"], unique=False, if_not_exists=True)
    op.create_index("ix_workflows_project_trigger", "workflows", ["project_id", "trigger_type"], unique=False, if_not_exists=True)

    op.create_table(
        "agent_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("proficiency_level", sa.Integer(), server_default="3", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_core", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.CheckConstraint("proficiency_level BETWEEN 1 AND 5", name="agent_skills_proficiency_between_1_and_5"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], name="fk_agent_skills_agent_id_agents", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_agent_skills"),
        sa.UniqueConstraint("agent_id", "name", name="uq_agent_skills_agent_id_name"),
        if_not_exists=True,
    )
    op.create_index("ix_agent_skills_agent_category", "agent_skills", ["agent_id", "category"], unique=False, if_not_exists=True)

    op.create_table(
        "agent_tool_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("invocation_timeout_seconds", sa.Integer(), server_default="30", nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], name="fk_agent_tool_links_agent_id_agents", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tool_id"], ["tools.id"], name="fk_agent_tool_links_tool_id_tools", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_agent_tool_links"),
        sa.UniqueConstraint("agent_id", "tool_id", name="uq_agent_tool_links_agent_id_tool_id"),
        if_not_exists=True,
    )
    op.create_index("ix_agent_tool_links_agent_enabled", "agent_tool_links", ["agent_id", "is_enabled"], unique=False, if_not_exists=True)

    op.create_table(
        "workflow_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tool_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("step_key", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("step_type", workflow_step_type, nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("retry_limit", sa.Integer(), server_default="0", nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), server_default="300", nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.ForeignKeyConstraint(["assigned_agent_id"], ["agents.id"], name="fk_workflow_steps_assigned_agent_id_agents", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tool_id"], ["tools.id"], name="fk_workflow_steps_tool_id_tools", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], name="fk_workflow_steps_workflow_id_workflows", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_workflow_steps"),
        sa.UniqueConstraint("workflow_id", "step_key", name="uq_workflow_steps_workflow_id_step_key"),
        sa.UniqueConstraint("workflow_id", "sequence", name="uq_workflow_steps_workflow_id_sequence"),
        if_not_exists=True,
    )
    op.create_index("ix_workflow_steps_workflow_sequence", "workflow_steps", ["workflow_id", "sequence"], unique=False, if_not_exists=True)
    op.create_index("ix_workflow_steps_assigned_agent_id", "workflow_steps", ["assigned_agent_id"], unique=False, if_not_exists=True)
    op.create_index("ix_workflow_steps_tool_id", "workflow_steps", ["tool_id"], unique=False, if_not_exists=True)

    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", task_priority, server_default="normal", nullable=False),
        sa.Column("status", task_status, server_default="queued", nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("input_payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("output_payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], name="fk_tasks_agent_id_agents", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name="fk_tasks_created_by_user_id_users", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_tasks_project_id_projects", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], name="fk_tasks_workflow_id_workflows", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_tasks"),
        if_not_exists=True,
    )
    op.create_index("ix_tasks_project_status_priority", "tasks", ["project_id", "status", "priority"], unique=False, if_not_exists=True)
    op.create_index("ix_tasks_agent_status", "tasks", ["agent_id", "status"], unique=False, if_not_exists=True)
    op.create_index("ix_tasks_workflow_status", "tasks", ["workflow_id", "status"], unique=False, if_not_exists=True)
    op.create_index("ix_tasks_due_at", "tasks", ["due_at"], unique=False, if_not_exists=True)

    op.create_table(
        "terminals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("status", terminal_status, server_default="idle", nullable=False),
        sa.Column("provider_ref", sa.String(length=255), nullable=True),
        sa.Column("capabilities", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], name="fk_terminals_agent_id_agents", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_terminals_project_id_projects", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], name="fk_terminals_task_id_tasks", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_terminals"),
        sa.UniqueConstraint("project_id", "name", name="uq_terminals_project_id_name"),
        if_not_exists=True,
    )
    op.create_index("ix_terminals_project_status", "terminals", ["project_id", "status"], unique=False, if_not_exists=True)
    op.create_index("ix_terminals_agent_status", "terminals", ["agent_id", "status"], unique=False, if_not_exists=True)

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", audit_action, nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("correlation_id", sa.String(length=120), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name="fk_audit_logs_actor_user_id_users", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_audit_logs_project_id_projects", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_audit_logs_tenant_id_tenants", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
        if_not_exists=True,
    )
    op.create_index("ix_audit_logs_tenant_entity", "audit_logs", ["tenant_id", "entity_type", "entity_id"], unique=False, if_not_exists=True)
    op.create_index("ix_audit_logs_project_action", "audit_logs", ["project_id", "action"], unique=False, if_not_exists=True)
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"], unique=False, if_not_exists=True)
    op.create_index("ix_audit_logs_correlation_id", "audit_logs", ["correlation_id"], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_audit_logs_correlation_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_project_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_tenant_entity", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_terminals_agent_status", table_name="terminals")
    op.drop_index("ix_terminals_project_status", table_name="terminals")
    op.drop_table("terminals")

    op.drop_index("ix_tasks_due_at", table_name="tasks")
    op.drop_index("ix_tasks_workflow_status", table_name="tasks")
    op.drop_index("ix_tasks_agent_status", table_name="tasks")
    op.drop_index("ix_tasks_project_status_priority", table_name="tasks")
    op.drop_table("tasks")

    op.drop_index("ix_workflow_steps_tool_id", table_name="workflow_steps")
    op.drop_index("ix_workflow_steps_assigned_agent_id", table_name="workflow_steps")
    op.drop_index("ix_workflow_steps_workflow_sequence", table_name="workflow_steps")
    op.drop_table("workflow_steps")

    op.drop_index("ix_agent_tool_links_agent_enabled", table_name="agent_tool_links")
    op.drop_table("agent_tool_links")

    op.drop_index("ix_agent_skills_agent_category", table_name="agent_skills")
    op.drop_table("agent_skills")

    op.drop_index("ix_workflows_project_trigger", table_name="workflows")
    op.drop_index("ix_workflows_project_status", table_name="workflows")
    op.drop_table("workflows")

    op.drop_index("ix_tools_project_type", table_name="tools")
    op.drop_index("ix_tools_project_enabled", table_name="tools")
    op.drop_table("tools")

    op.drop_index("ix_agents_project_model", table_name="agents")
    op.drop_index("ix_agents_project_status", table_name="agents")
    op.drop_table("agents")

    op.drop_index("ix_projects_owner_user_id", table_name="projects")
    op.drop_index("ix_projects_tenant_status", table_name="projects")
    op.drop_table("projects")

    op.drop_index("ix_users_tenant_role", table_name="users")
    op.drop_index("ix_users_tenant_status", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_tenants_status", table_name="tenants")
    op.drop_table("tenants")

    bind = op.get_bind()
    audit_action.drop(bind, checkfirst=True)
    tool_type.drop(bind, checkfirst=True)
    terminal_status.drop(bind, checkfirst=True)
    workflow_step_type.drop(bind, checkfirst=True)
    workflow_trigger_type.drop(bind, checkfirst=True)
    workflow_status.drop(bind, checkfirst=True)
    task_status.drop(bind, checkfirst=True)
    task_priority.drop(bind, checkfirst=True)
    agent_status.drop(bind, checkfirst=True)
    project_status.drop(bind, checkfirst=True)
    user_status.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)
    tenant_status.drop(bind, checkfirst=True)
