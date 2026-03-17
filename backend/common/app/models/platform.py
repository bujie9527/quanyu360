from __future__ import annotations

import enum
import uuid
from typing import Any

from sqlalchemy import Boolean
from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from common.app.db.base import Base


class TimestampedUUIDModel(Base):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[Any] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[Any] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class TenantStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    archived = "archived"


class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    operator = "operator"


class UserStatus(str, enum.Enum):
    invited = "invited"
    active = "active"
    disabled = "disabled"


class ProjectStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    archived = "archived"


class ProjectType(str, enum.Enum):
    general = "general"
    matrix_site = "matrix_site"


class AgentStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    paused = "paused"
    archived = "archived"


class TaskPriority(str, enum.Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class TaskStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class TeamExecutionType(str, enum.Enum):
    sequential = "sequential"
    parallel = "parallel"
    review_loop = "review_loop"


class WorkflowStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    archived = "archived"


class WorkflowTriggerType(str, enum.Enum):
    manual = "manual"
    scheduled = "scheduled"
    webhook = "webhook"
    event = "event"


class WorkflowStepType(str, enum.Enum):
    agent_task = "agent_task"
    tool_call = "tool_call"
    condition = "condition"
    delay = "delay"


class TerminalStatus(str, enum.Enum):
    idle = "idle"
    connected = "connected"
    busy = "busy"
    offline = "offline"
    terminated = "terminated"


class ToolType(str, enum.Enum):
    api = "api"
    terminal = "terminal"
    knowledge = "knowledge"
    integration = "integration"


class AssetKind(str, enum.Enum):
    file = "file"
    document = "document"
    image = "image"


class AuditAction(str, enum.Enum):
    create = "create"
    update = "update"
    delete = "delete"
    execute = "execute"
    assign = "assign"
    login = "login"


class UsageType(str, enum.Enum):
    llm_tokens = "llm_tokens"
    workflow_run = "workflow_run"
    tool_execution = "tool_execution"


class RbacRoleSlug(str, enum.Enum):
    platform_admin = "platform_admin"
    tenant_admin = "tenant_admin"
    operator = "operator"
    viewer = "viewer"


class WordPressSiteStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    error = "error"


class PlatformDomainStatus(str, enum.Enum):
    """骞冲彴鍩熷悕姹犵姸鎬併€俛vailable=鍙敤锛宎ssigned=宸插垎閰嶏紝inactive=鍋滅敤"""
    available = "available"
    assigned = "assigned"
    inactive = "inactive"


class ServerStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class SitePlanStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    executing = "executing"


class SitePlanItemStatus(str, enum.Enum):
    planned = "planned"
    building = "building"
    active = "active"


class ContentSourceType(str, enum.Enum):
    api = "api"
    rss = "rss"


class Tenant(TimestampedUUIDModel):
    __tablename__ = "tenants"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_tenants_slug"),
        Index("ix_tenants_status", "status"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[TenantStatus] = mapped_column(
        Enum(TenantStatus, name="tenant_status"),
        nullable=False,
        default=TenantStatus.active,
        server_default=TenantStatus.active.value,
    )
    plan_name: Mapped[str] = mapped_column(String(80), nullable=False, default="mvp", server_default="mvp")
    settings: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    users: Mapped[list["User"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    usage_logs: Mapped[list["UsageLog"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    assets: Mapped[list["Asset"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    wordpress_sites: Mapped[list["WordPressSite"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    content_sources: Mapped[list["ContentSource"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    agent_instances: Mapped[list["AgentInstance"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class User(TimestampedUUIDModel):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_id_email"),
        Index("ix_users_tenant_status", "tenant_id", "status"),
        Index("ix_users_tenant_role", "tenant_id", "role"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(CITEXT(), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        nullable=False,
        default=UserRole.operator,
        server_default=UserRole.operator.value,
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status"),
        nullable=False,
        default=UserStatus.invited,
        server_default=UserStatus.invited.value,
    )
    last_login_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="users")
    role_assignments: Mapped[list["UserRoleAssignment"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    owned_projects: Mapped[list["Project"]] = relationship(back_populates="owner")
    project_memberships: Mapped[list["ProjectTeamMember"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    created_agents: Mapped[list["Agent"]] = relationship(back_populates="created_by")
    created_tasks: Mapped[list["Task"]] = relationship(back_populates="created_by")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="actor_user")


class Project(TimestampedUUIDModel):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("tenant_id", "key", name="uq_projects_tenant_id_key"),
        Index("ix_projects_tenant_status", "tenant_id", "status"),
        Index("ix_projects_owner_user_id", "owner_user_id"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    key: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status"),
        nullable=False,
        default=ProjectStatus.draft,
        server_default=ProjectStatus.draft.value,
    )
    project_type: Mapped[ProjectType] = mapped_column(
        Enum(ProjectType, name="project_type"),
        nullable=False,
        default=ProjectType.general,
        server_default=ProjectType.general.value,
    )
    matrix_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="projects")
    owner: Mapped["User | None"] = relationship(back_populates="owned_projects")
    team_memberships: Mapped[list["ProjectTeamMember"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    agents: Mapped[list["Agent"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    workflows: Mapped[list["Workflow"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    task_templates: Mapped[list["TaskTemplate"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    terminals: Mapped[list["Terminal"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    tools: Mapped[list["Tool"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    assets: Mapped[list["Asset"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    knowledge_bases: Mapped[list["KnowledgeBase"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    agent_teams: Mapped[list["AgentTeam"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    wordpress_sites: Mapped[list["WordPressSite"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    site_plans: Mapped[list["SitePlan"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    agent_instances: Mapped[list["AgentInstance"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="project")


class ProjectTeamMember(TimestampedUUIDModel):
    __tablename__ = "project_team_members"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_team_members_project_id_user_id"),
        Index("ix_project_team_members_project_id", "project_id"),
        Index("ix_project_team_members_user_id", "user_id"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_type=False),
        nullable=False,
        default=UserRole.operator,
        server_default=UserRole.operator.value,
    )

    project: Mapped["Project"] = relationship(back_populates="team_memberships")
    user: Mapped["User"] = relationship(back_populates="project_memberships")


class Agent(TimestampedUUIDModel):
    __tablename__ = "agents"
    __table_args__ = (
        UniqueConstraint("project_id", "slug", name="uq_agents_project_id_slug"),
        Index("ix_agents_project_status", "project_id", "status"),
        Index("ix_agents_project_model", "project_id", "model"),
        Index("ix_agents_project_role", "project_id", "role"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(120), nullable=False)
    role_title: Mapped[str] = mapped_column(String(120), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus, name="agent_status"),
        nullable=False,
        default=AgentStatus.draft,
        server_default=AgentStatus.draft.value,
    )
    max_concurrency: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    project: Mapped["Project"] = relationship(back_populates="agents")
    created_by: Mapped["User | None"] = relationship(back_populates="created_agents")
    skills: Mapped[list["AgentSkill"]] = relationship(
        back_populates="agent",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    tool_links: Mapped[list["AgentToolLink"]] = relationship(
        back_populates="agent",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    tool_permissions: Mapped[list["AgentToolPermission"]] = relationship(
        back_populates="agent",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    workflow_links: Mapped[list["AgentWorkflowLink"]] = relationship(
        back_populates="agent",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    tools: Mapped[list["Tool"]] = relationship(
        secondary="agent_tool_links",
        back_populates="agents",
        viewonly=True,
    )
    workflows: Mapped[list["Workflow"]] = relationship(
        secondary="agent_workflow_links",
        back_populates="agents",
        viewonly=True,
    )
    tasks: Mapped[list["Task"]] = relationship(back_populates="agent")
    workflow_steps: Mapped[list["WorkflowStep"]] = relationship(back_populates="assigned_agent")
    terminals: Mapped[list["Terminal"]] = relationship(back_populates="agent")
    team_memberships: Mapped[list["AgentTeamMember"]] = relationship(
        back_populates="agent",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reflections: Mapped[list["AgentReflection"]] = relationship(
        back_populates="agent",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AgentTeam(TimestampedUUIDModel):
    """Multi-agent team for collaborative execution (e.g. Content Team: Writer, Editor, Publisher)."""
    __tablename__ = "agent_teams"
    __table_args__ = (
        UniqueConstraint("project_id", "slug", name="uq_agent_teams_project_id_slug"),
        Index("ix_agent_teams_project_execution", "project_id", "execution_type"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_type: Mapped[TeamExecutionType] = mapped_column(
        Enum(TeamExecutionType, name="team_execution_type"),
        nullable=False,
        default=TeamExecutionType.sequential,
        server_default=TeamExecutionType.sequential.value,
    )

    project: Mapped["Project"] = relationship(back_populates="agent_teams")
    tasks: Mapped[list["Task"]] = relationship(back_populates="team")
    members: Mapped[list["AgentTeamMember"]] = relationship(
        back_populates="team",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AgentTeamMember.order_index",
    )


class AgentTeamMember(TimestampedUUIDModel):
    """Member of an agent team with order and role (e.g. writer, editor, publisher)."""
    __tablename__ = "agent_team_members"
    __table_args__ = (
        UniqueConstraint("team_id", "agent_id", name="uq_agent_team_members_team_id_agent_id"),
        Index("ix_agent_team_members_team_id", "team_id"),
        Index("ix_agent_team_members_agent_id", "agent_id"),
    )

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    role_in_team: Mapped[str] = mapped_column(String(120), nullable=False)

    team: Mapped["AgentTeam"] = relationship(back_populates="members")
    agent: Mapped["Agent"] = relationship(back_populates="team_memberships")


class AgentTemplate(TimestampedUUIDModel):
    """Agent 妯℃澘锛氶璁?system_prompt銆乵odel銆乨efault_tools銆乨efault_workflows 绛夈€傜敤浜庡揩閫熷垱寤?Agent銆?""

    __tablename__ = "agent_templates"
    __table_args__ = (
        Index("ix_agent_templates_enabled", "enabled"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    model: Mapped[str] = mapped_column(String(120), nullable=False, default="gpt-4", server_default="gpt-4")
    default_tools: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    default_workflows: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    config_schema: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))

    instances: Mapped[list["AgentInstance"]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AgentInstance(TimestampedUUIDModel):
    """Agent 瀹炰緥锛氫粠 AgentTemplate 澶嶅埗閰嶇疆锛屾敮鎸?tools_override銆乻ystem_prompt 瑕嗙洊銆?""

    __tablename__ = "agent_instances"
    __table_args__ = (
        Index("ix_agent_instances_tenant_id", "tenant_id"),
        Index("ix_agent_instances_project_id", "project_id"),
        Index("ix_agent_instances_template_id", "template_id"),
        Index("ix_agent_instances_enabled", "enabled"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    model: Mapped[str] = mapped_column(String(120), nullable=False, default="gpt-4", server_default="gpt-4")
    tools_override: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    knowledge_base_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="SET NULL"),
        nullable=True,
    )
    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))

    tenant: Mapped["Tenant"] = relationship(back_populates="agent_instances")
    project: Mapped["Project"] = relationship(back_populates="agent_instances")
    template: Mapped["AgentTemplate | None"] = relationship(back_populates="instances")
    knowledge_base: Mapped["KnowledgeBase | None"] = relationship(back_populates="agent_instances")


class AgentRun(TimestampedUUIDModel):
    """Agent 鎵ц鏃ュ織锛氭瘡娆?run_task / run_workflow / run_task_template 蹇呴』鍐欏叆銆?""
    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("ix_agent_runs_agent_id", "agent_id"),
        Index("ix_agent_runs_status", "status"),
        Index("ix_agent_runs_created_at", "created_at"),
    )

    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False, server_default="chat")
    input: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    output: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    status: Mapped[str] = mapped_column(String(32), nullable=False)


class AgentSkill(TimestampedUUIDModel):
    __tablename__ = "agent_skills"
    __table_args__ = (
        UniqueConstraint("agent_id", "name", name="uq_agent_skills_agent_id_name"),
        CheckConstraint("proficiency_level BETWEEN 1 AND 5", name="agent_skills_proficiency_between_1_and_5"),
        Index("ix_agent_skills_agent_category", "agent_id", "category"),
    )

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    proficiency_level: Mapped[int] = mapped_column(Integer, nullable=False, default=3, server_default="3")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_core: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))

    agent: Mapped["Agent"] = relationship(back_populates="skills")


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    embedded = "embedded"
    failed = "failed"


class KnowledgeBase(TimestampedUUIDModel):
    """Project-scoped knowledge base for RAG: documents + embeddings in Qdrant."""
    __tablename__ = "knowledge_bases"
    __table_args__ = (
        UniqueConstraint("project_id", "slug", name="uq_knowledge_bases_project_id_slug"),
        Index("ix_knowledge_bases_project", "project_id"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_model: Mapped[str] = mapped_column(
        String(80), nullable=False, default="text-embedding-3-small", server_default="text-embedding-3-small"
    )
    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    project: Mapped["Project"] = relationship(back_populates="knowledge_bases")
    agent_instances: Mapped[list["AgentInstance"]] = relationship(
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Document(TimestampedUUIDModel):
    """Uploaded document for a knowledge base."""
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_knowledge_base_status", "knowledge_base_id", "status"),
    )

    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"),
        nullable=False,
        default=DocumentStatus.pending,
        server_default=DocumentStatus.pending.value,
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    knowledge_base: Mapped["KnowledgeBase"] = relationship(back_populates="documents")
    embeddings: Mapped[list["DocumentEmbedding"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class DocumentEmbedding(TimestampedUUIDModel):
    """Embedding record: links document chunk to Qdrant point."""
    __tablename__ = "document_embeddings"
    __table_args__ = (
        Index("ix_document_embeddings_document", "document_id"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    qdrant_point_id: Mapped[str] = mapped_column(String(64), nullable=False)

    document: Mapped["Document"] = relationship(back_populates="embeddings")


class Asset(TimestampedUUIDModel):
    __tablename__ = "assets"
    __table_args__ = (
        Index("ix_assets_tenant_project", "tenant_id", "project_id"),
        Index("ix_assets_project_kind", "project_id", "kind"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    kind: Mapped[AssetKind] = mapped_column(
        Enum(AssetKind, name="asset_kind"),
        nullable=False,
        default=AssetKind.file,
        server_default=AssetKind.file.value,
    )
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="assets")
    project: Mapped["Project"] = relationship(back_populates="assets")


class Tool(TimestampedUUIDModel):
    __tablename__ = "tools"
    __table_args__ = (
        UniqueConstraint("project_id", "slug", name="uq_tools_project_id_slug"),
        Index("ix_tools_project_enabled", "project_id", "is_enabled"),
        Index("ix_tools_project_type", "project_id", "tool_type"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    tool_type: Mapped[ToolType] = mapped_column(
        Enum(ToolType, name="tool_type"),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))

    project: Mapped["Project"] = relationship(back_populates="tools")
    workflow_steps: Mapped[list["WorkflowStep"]] = relationship(back_populates="tool")
    agent_links: Mapped[list["AgentToolLink"]] = relationship(
        back_populates="tool",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    agents: Mapped[list["Agent"]] = relationship(
        secondary="agent_tool_links",
        back_populates="tools",
        viewonly=True,
    )


class AgentToolLink(TimestampedUUIDModel):
    __tablename__ = "agent_tool_links"
    __table_args__ = (
        UniqueConstraint("agent_id", "tool_id", name="uq_agent_tool_links_agent_id_tool_id"),
        Index("ix_agent_tool_links_agent_enabled", "agent_id", "is_enabled"),
    )

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    tool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tools.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    invocation_timeout_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
        server_default="30",
    )

    agent: Mapped["Agent"] = relationship(back_populates="tool_links")
    tool: Mapped["Tool"] = relationship(back_populates="agent_links")


class AgentToolPermission(TimestampedUUIDModel):
    """Explicit permission: agent can use runtime tool by slug (e.g. wordpress, facebook, seo)."""
    __tablename__ = "agent_tool_permissions"
    __table_args__ = (
        UniqueConstraint("agent_id", "tool_slug", name="uq_agent_tool_permissions_agent_id_tool_slug"),
        Index("ix_agent_tool_permissions_agent_id", "agent_id"),
        Index("ix_agent_tool_permissions_tool_slug", "tool_slug"),
    )

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    tool_slug: Mapped[str] = mapped_column(String(120), nullable=False)

    agent: Mapped["Agent"] = relationship(back_populates="tool_permissions")


class AgentWorkflowLink(TimestampedUUIDModel):
    __tablename__ = "agent_workflow_links"
    __table_args__ = (
        UniqueConstraint("agent_id", "workflow_id", name="uq_agent_workflow_links_agent_id_workflow_id"),
        Index("ix_agent_workflow_links_agent_id", "agent_id"),
        Index("ix_agent_workflow_links_workflow_id", "workflow_id"),
    )

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
    )

    agent: Mapped["Agent"] = relationship(back_populates="workflow_links")
    workflow: Mapped["Workflow"] = relationship(back_populates="agent_links")


class PlatformDomain(TimestampedUUIDModel):
    """骞冲彴缁熶竴閰嶇疆鐨勫煙鍚嶆睜锛屾瘡涓煙鍚嶅凡鍋氬ソ DNS 瑙ｆ瀽鍜?SSL 閰嶇疆銆?""
    __tablename__ = "platform_domains"
    __table_args__ = (
        Index("ix_platform_domains_status", "status"),
        UniqueConstraint("domain", name="uq_platform_domains_domain"),
    )

    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    api_base_url: Mapped[str] = mapped_column(String(512), nullable=False)
    server_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("servers.id", ondelete="SET NULL"),
        nullable=True,
    )
    ssl_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    status: Mapped[PlatformDomainStatus] = mapped_column(
        Enum(PlatformDomainStatus, name="platform_domain_status"),
        nullable=False,
        default=PlatformDomainStatus.available,
        server_default=PlatformDomainStatus.available.value,
    )
    server: Mapped["Server | None"] = relationship(back_populates="platform_domains")


class Server(TimestampedUUIDModel):
    __tablename__ = "servers"
    __table_args__ = (
        UniqueConstraint("name", name="uq_servers_name"),
        Index("ix_servers_status", "status"),
        Index("ix_servers_host_port", "host", "port"),
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False, default=22, server_default="22")
    ssh_user: Mapped[str] = mapped_column(String(120), nullable=False)
    ssh_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ssh_private_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    web_root: Mapped[str] = mapped_column(String(512), nullable=False)
    php_bin: Mapped[str] = mapped_column(String(255), nullable=False, default="php", server_default="php")
    wp_cli_bin: Mapped[str] = mapped_column(String(255), nullable=False, default="wp", server_default="wp")
    mysql_host: Mapped[str] = mapped_column(String(255), nullable=False, default="localhost", server_default="localhost")
    mysql_port: Mapped[int] = mapped_column(Integer, nullable=False, default=3306, server_default="3306")
    mysql_admin_user: Mapped[str] = mapped_column(String(120), nullable=False)
    mysql_admin_password: Mapped[str] = mapped_column(String(255), nullable=False)
    mysql_db_prefix: Mapped[str] = mapped_column(String(32), nullable=False, default="wp_", server_default="wp_")
    status: Mapped[ServerStatus] = mapped_column(
        Enum(ServerStatus, name="server_status"),
        nullable=False,
        default=ServerStatus.active,
        server_default=ServerStatus.active.value,
    )

    platform_domains: Mapped[list["PlatformDomain"]] = relationship(back_populates="server")


class SitePlan(TimestampedUUIDModel):
    __tablename__ = "site_plans"
    __table_args__ = (
        Index("ix_site_plans_project_id", "project_id"),
        Index("ix_site_plans_status", "status"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[SitePlanStatus] = mapped_column(
        Enum(SitePlanStatus, name="site_plan_status"),
        nullable=False,
        default=SitePlanStatus.draft,
        server_default=SitePlanStatus.draft.value,
    )
    agent_input: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    agent_output: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    approved_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="site_plans")
    items: Mapped[list["SitePlanItem"]] = relationship(
        back_populates="site_plan",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SitePlanItem.created_at",
    )


class SitePlanItem(TimestampedUUIDModel):
    __tablename__ = "site_plan_items"
    __table_args__ = (
        Index("ix_site_plan_items_site_plan_id", "site_plan_id"),
        Index("ix_site_plan_items_status", "status"),
        Index("ix_site_plan_items_wordpress_site_id", "wordpress_site_id"),
    )

    site_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("site_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    site_name: Mapped[str] = mapped_column(String(255), nullable=False)
    site_theme: Mapped[str] = mapped_column(String(255), nullable=False)
    target_audience: Mapped[str] = mapped_column(Text, nullable=False)
    content_direction: Mapped[str] = mapped_column(Text, nullable=False)
    seo_keywords: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    site_structure: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    wordpress_site_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("wordpress_sites.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[SitePlanItemStatus] = mapped_column(
        Enum(SitePlanItemStatus, name="site_plan_item_status"),
        nullable=False,
        default=SitePlanItemStatus.planned,
        server_default=SitePlanItemStatus.planned.value,
    )

    site_plan: Mapped["SitePlan"] = relationship(back_populates="items")


class WordPressSite(TimestampedUUIDModel):
    __tablename__ = "wordpress_sites"
    __table_args__ = (
        Index("ix_wordpress_sites_tenant_id", "tenant_id"),
        Index("ix_wordpress_sites_project_id", "project_id"),
        Index("ix_wordpress_sites_server_id", "server_id"),
        Index("ix_wordpress_sites_install_task_run_id", "install_task_run_id"),
    )

    platform_domain_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("platform_domains.id", ondelete="SET NULL"),
        nullable=True,
    )
    server_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("servers.id", ondelete="SET NULL"),
        nullable=True,
    )
    install_task_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    api_url: Mapped[str] = mapped_column(String(512), nullable=False)
    username: Mapped[str] = mapped_column(String(120), nullable=False)
    app_password: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[WordPressSiteStatus] = mapped_column(
        Enum(WordPressSiteStatus, name="wordpress_site_status"),
        nullable=False,
        default=WordPressSiteStatus.active,
        server_default=WordPressSiteStatus.active.value,
    )

    tenant: Mapped["Tenant | None"] = relationship(back_populates="wordpress_sites")
    project: Mapped["Project | None"] = relationship(back_populates="wordpress_sites")


class ContentSource(TimestampedUUIDModel):
    """鍐呭婧愰厤缃細API 鎴?RSS锛岀敤浜庣粺涓€鎷夊彇鍐呭銆?""

    __tablename__ = "content_sources"
    __table_args__ = (
        Index("ix_content_sources_tenant_id", "tenant_id"),
        Index("ix_content_sources_type_enabled", "type", "enabled"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[ContentSourceType] = mapped_column(
        Enum(ContentSourceType, name="content_source_type"),
        nullable=False,
    )
    api_endpoint: Mapped[str] = mapped_column(String(512), nullable=False)
    auth: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    schema: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))

    tenant: Mapped["Tenant"] = relationship(back_populates="content_sources")


class Workflow(TimestampedUUIDModel):
    __tablename__ = "workflows"
    __table_args__ = (
        UniqueConstraint("project_id", "slug", "version", name="uq_workflows_project_id_slug_version"),
        Index("ix_workflows_project_status", "project_id", "status"),
        Index("ix_workflows_project_trigger", "project_id", "trigger_type"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus, name="workflow_status"),
        nullable=False,
        default=WorkflowStatus.draft,
        server_default=WorkflowStatus.draft.value,
    )
    trigger_type: Mapped[WorkflowTriggerType] = mapped_column(
        Enum(WorkflowTriggerType, name="workflow_trigger_type"),
        nullable=False,
        default=WorkflowTriggerType.manual,
        server_default=WorkflowTriggerType.manual.value,
    )
    definition: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    published_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="workflows")
    task_templates: Mapped[list["TaskTemplate"]] = relationship(
        back_populates="workflow",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="TaskTemplate.workflow_id",
    )
    agent_links: Mapped[list["AgentWorkflowLink"]] = relationship(
        back_populates="workflow",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    agents: Mapped[list["Agent"]] = relationship(
        secondary="agent_workflow_links",
        back_populates="workflows",
        viewonly=True,
    )
    steps: Mapped[list["WorkflowStep"]] = relationship(
        back_populates="workflow",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="WorkflowStep.sequence",
    )
    tasks: Mapped[list["Task"]] = relationship(back_populates="workflow")
    task_runs: Mapped[list["TaskRun"]] = relationship(
        back_populates="workflow",
        cascade="all, delete-orphan",
    )


class TaskTemplate(TimestampedUUIDModel):
    """浠诲姟妯℃澘锛屽彲缁戝畾 Workflow锛屽畾涔夊垱寤轰换鍔℃椂鐨勫弬鏁扮粨鏋勩€?""

    __tablename__ = "task_templates"
    __table_args__ = (
        Index("ix_task_templates_project_id", "project_id"),
        Index("ix_task_templates_workflow_id", "workflow_id"),
        Index("ix_task_templates_enabled", "enabled"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="SET NULL"),
        nullable=True,
    )
    parameters_schema: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))

    project: Mapped["Project"] = relationship(back_populates="task_templates")
    workflow: Mapped["Workflow | None"] = relationship(
        back_populates="task_templates",
        foreign_keys=[workflow_id],
    )
    schedules: Mapped[list["Schedule"]] = relationship(
        back_populates="task_template",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    task_runs: Mapped[list["TaskRun"]] = relationship(
        back_populates="task_template",
        cascade="all, delete-orphan",
    )


class Schedule(TimestampedUUIDModel):
    """瀹氭椂浠诲姟锛氭寜 cron 瑙﹀彂 task_template 缁戝畾鐨?workflow锛屽彲鎸囧畾 target_sites銆?""

    __tablename__ = "schedules"
    __table_args__ = (
        Index("ix_schedules_task_template_id", "task_template_id"),
        Index("ix_schedules_enabled", "enabled"),
    )

    task_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    cron: Mapped[str] = mapped_column(String(60), nullable=False)
    target_sites: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))

    task_template: Mapped["TaskTemplate"] = relationship(back_populates="schedules")


class TaskRun(TimestampedUUIDModel):
    """Execution log: 涓€娆?task_template 鎴?workflow 鐨勮繍琛岃褰曘€?""

    __tablename__ = "task_runs"
    __table_args__ = (
        Index("ix_task_runs_task_template_id", "task_template_id"),
        Index("ix_task_runs_workflow_id", "workflow_id"),
        Index("ix_task_runs_status", "status"),
    )

    task_template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
    )
    execution_id: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    start_time: Mapped[Any] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    end_time: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)

    task_template: Mapped["TaskTemplate | None"] = relationship(back_populates="task_runs")
    workflow: Mapped["Workflow"] = relationship(back_populates="task_runs")
    step_runs: Mapped[list["StepRun"]] = relationship(
        back_populates="task_run",
        cascade="all, delete-orphan",
        order_by="StepRun.created_at",
    )


class StepRun(TimestampedUUIDModel):
    """Workflow 鍗曟鎵ц璁板綍銆傛瘡涓?workflow 姝ラ蹇呴』鍐欏叆銆?""

    __tablename__ = "step_runs"
    __table_args__ = (
        Index("ix_step_runs_task_run_id", "task_run_id"),
    )

    task_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    duration: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    output_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    task_run: Mapped["TaskRun"] = relationship(back_populates="step_runs")


class WorkflowStep(TimestampedUUIDModel):
    __tablename__ = "workflow_steps"
    __table_args__ = (
        UniqueConstraint("workflow_id", "step_key", name="uq_workflow_steps_workflow_id_step_key"),
        UniqueConstraint("workflow_id", "sequence", name="uq_workflow_steps_workflow_id_sequence"),
        Index("ix_workflow_steps_workflow_sequence", "workflow_id", "sequence"),
        Index("ix_workflow_steps_assigned_agent_id", "assigned_agent_id"),
        Index("ix_workflow_steps_tool_id", "tool_id"),
    )

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
    )
    assigned_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
    )
    tool_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tools.id", ondelete="SET NULL"),
        nullable=True,
    )
    step_key: Mapped[str] = mapped_column(String(120), nullable=False)
    next_step_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    step_type: Mapped[WorkflowStepType] = mapped_column(
        Enum(WorkflowStepType, name="workflow_step_type"),
        nullable=False,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    retry_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=300, server_default="300")
    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    workflow: Mapped["Workflow"] = relationship(back_populates="steps")
    assigned_agent: Mapped["Agent | None"] = relationship(back_populates="workflow_steps")
    tool: Mapped["Tool | None"] = relationship(back_populates="workflow_steps")


class Task(TimestampedUUIDModel):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_project_status_priority", "project_id", "status", "priority"),
        Index("ix_tasks_agent_status", "agent_id", "status"),
        Index("ix_tasks_workflow_status", "workflow_id", "status"),
        Index("ix_tasks_team_id", "team_id"),
        Index("ix_tasks_due_at", "due_at"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, name="task_priority"),
        nullable=False,
        default=TaskPriority.normal,
        server_default=TaskPriority.normal.value,
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status"),
        nullable=False,
        default=TaskStatus.pending,
        server_default=TaskStatus.pending.value,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3, server_default="3")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)
    input_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    output_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    project: Mapped["Project"] = relationship(back_populates="tasks")
    agent: Mapped["Agent | None"] = relationship(back_populates="tasks")
    team: Mapped["AgentTeam | None"] = relationship(back_populates="tasks")
    workflow: Mapped["Workflow | None"] = relationship(back_populates="tasks")
    created_by: Mapped["User | None"] = relationship(back_populates="created_tasks")
    terminals: Mapped[list["Terminal"]] = relationship(back_populates="task")
    reflections: Mapped[list["AgentReflection"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AgentReflection(TimestampedUUIDModel):
    """Agent self-evaluation after task execution. Improves next run."""

    __tablename__ = "agent_reflections"
    __table_args__ = (
        Index("ix_agent_reflections_task_id", "task_id"),
        Index("ix_agent_reflections_agent_id", "agent_id"),
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
    )
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    issues: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    improvement: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")

    task: Mapped["Task"] = relationship(back_populates="reflections")
    agent: Mapped["Agent | None"] = relationship(back_populates="reflections")


class Terminal(TimestampedUUIDModel):
    __tablename__ = "terminals"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_terminals_project_id_name"),
        Index("ix_terminals_project_status", "project_id", "status"),
        Index("ix_terminals_agent_status", "agent_id", "status"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[TerminalStatus] = mapped_column(
        Enum(TerminalStatus, name="terminal_status"),
        nullable=False,
        default=TerminalStatus.idle,
        server_default=TerminalStatus.idle.value,
    )
    provider_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    capabilities: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    last_seen_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="terminals")
    agent: Mapped["Agent | None"] = relationship(back_populates="terminals")
    task: Mapped["Task | None"] = relationship(back_populates="terminals")


class AuditLog(TimestampedUUIDModel):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_tenant_entity", "tenant_id", "entity_type", "entity_id"),
        Index("ix_audit_logs_project_action", "project_id", "action"),
        Index("ix_audit_logs_actor_user_id", "actor_user_id"),
        Index("ix_audit_logs_correlation_id", "correlation_id"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="audit_action"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="audit_logs")
    project: Mapped["Project | None"] = relationship(back_populates="audit_logs")
    actor_user: Mapped["User | None"] = relationship(back_populates="audit_logs")


class UsageLog(TimestampedUUIDModel):
    """Usage tracking per tenant: LLM tokens, workflow runs, tool executions."""
    __tablename__ = "usage_logs"
    __table_args__ = (
        Index("ix_usage_logs_tenant_type", "tenant_id", "usage_type"),
        Index("ix_usage_logs_tenant_created", "tenant_id", "created_at"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    usage_type: Mapped[UsageType] = mapped_column(
        Enum(UsageType, name="usage_type"),
        nullable=False,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="usage_logs")
    project: Mapped["Project | None"] = relationship()


# --- RBAC ---

class Role(TimestampedUUIDModel):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("slug", name="uq_roles_slug"),)

    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    permissions: Mapped[list["Permission"]] = relationship(
        secondary="role_permissions",
        back_populates="roles",
    )


class Permission(TimestampedUUIDModel):
    __tablename__ = "permissions"
    __table_args__ = (UniqueConstraint("slug", name="uq_permissions_slug"),)

    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    resource: Mapped[str] = mapped_column(String(80), nullable=False)
    action: Mapped[str] = mapped_column(String(40), nullable=False)

    roles: Mapped[list["Role"]] = relationship(
        secondary="role_permissions",
        back_populates="permissions",
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_permission"),
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )


class UserRoleAssignment(TimestampedUUIDModel):
    __tablename__ = "user_role_assignments"
    __table_args__ = (
        Index("ix_user_role_assignments_user", "user_id"),
        Index("ix_user_role_assignments_tenant", "tenant_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
    )

    user: Mapped["User"] = relationship(back_populates="role_assignments")
    role: Mapped["Role"] = relationship()
    tenant: Mapped["Tenant | None"] = relationship()


class SystemConfig(TimestampedUUIDModel):
    """Platform-wide system configuration (env vars, API keys, etc.)."""

    __tablename__ = "system_configs"
    __table_args__ = (UniqueConstraint("key", name="uq_system_configs_key"),)

    key: Mapped[str] = mapped_column(String(120), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    is_secret: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)


