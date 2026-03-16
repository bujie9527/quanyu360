from __future__ import annotations

import uuid
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from common.app.models import Agent
from common.app.models import AgentSkill
from common.app.models import AgentTemplate
from common.app.models import AgentStatus
from common.app.models import AgentToolLink
from common.app.models import AgentToolPermission
from common.app.models import AgentWorkflowLink
from common.app.models import AuditAction
from common.app.models import AuditLog
from common.app.models import Project
from common.app.models import ProjectTeamMember
from common.app.models import ProjectStatus
from common.app.models import Task
from common.app.models import TaskPriority
from common.app.models import TaskStatus
from common.app.models import Tenant
from common.app.models import TenantStatus
from common.app.models import Terminal
from common.app.models import TerminalStatus
from common.app.models import Tool
from common.app.models import ToolType
from common.app.models import Permission
from common.app.models import Role
from common.app.models import User
from common.app.models import UserRole
from common.app.models import UserStatus
from common.app.models import Workflow
from common.app.models import WorkflowStatus
from common.app.models import WorkflowStep
from common.app.models import WorkflowStepType
from common.app.models import WorkflowTriggerType

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

RBAC_ROLES = [
    ("platform_admin", "Platform Admin", "Full platform access across all tenants"),
    ("tenant_admin", "Tenant Admin", "Full access within assigned tenant(s)"),
    ("operator", "Operator", "Can run agents, tasks, workflows"),
    ("viewer", "Viewer", "Read-only access"),
]

RBAC_PERMISSIONS = [
    ("tenants:manage", "tenants", "manage"),
    ("tenants:read", "tenants", "read"),
    ("roles:manage", "roles", "manage"),
    ("users:manage", "users", "manage"),
    ("projects:*", "projects", "*"),
    ("agents:*", "agents", "*"),
    ("tasks:*", "tasks", "*"),
    ("workflows:*", "workflows", "*"),
]


def seed_rbac_roles(session: Session) -> None:
    """Create default RBAC roles and permissions if they don't exist."""
    for slug, name, desc in RBAC_ROLES:
        if session.scalar(select(Role).where(Role.slug == slug)):
            continue
        session.add(Role(slug=slug, name=name, description=desc))
    session.flush()
    for slug, resource, action in RBAC_PERMISSIONS:
        if session.scalar(select(Permission).where(Permission.slug == slug)):
            continue
        session.add(Permission(slug=slug, resource=resource, action=action))
    session.commit()


# 固定 UUID，确保 auth_db / project_db 等多库 seed 后 tenant/owner 一致
DEMO_TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DEMO_OWNER_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")

# AgentTemplate 初始化：平台级模板，可独立于 demo 租户运行
AGENT_TEMPLATES = [
    {
        "name": "WordPress Builder Agent",
        "description": "WordPress 站点构建与插件安装。",
        "default_tools": ["server.create", "wordpress.install", "wordpress.install_plugin"],
    },
    {
        "name": "Site Operator Agent",
        "description": "站点内容抓取、SEO 与 WordPress 发布。",
        "default_tools": ["content.fetch", "seo.generate_meta", "wordpress.publish_post", "wordpress.create_comment"],
    },
    {
        "name": "Facebook Operator Agent",
        "description": "Facebook 发帖、评论与私信。",
        "default_tools": ["facebook.publish_post", "facebook.comment", "facebook.message"],
    },
    {
        "name": "矩阵站规划师",
        "description": "根据品牌和目标用户生成多站点矩阵规划方案。",
        "model": "gpt-4.1",
        "default_tools": [],
        "default_workflows": [],
        "system_prompt": (
            "你是海外矩阵站内容规划专家。"
            "输入将包含品牌、产品类型、目标市场、推广目标与目标人群。"
            "你需要输出可执行的多站点规划，并使用结构化 JSON。"
            "每个站点必须包含：site_name, site_theme, target_audience, content_direction, "
            "seo_keywords(数组), site_structure(对象)。"
            "要求各站点主题差异化，覆盖不同搜索意图（资讯、评测、购买指南、品牌故事、圈层文化等），"
            "并强调长期内容资产沉淀与品牌词搜索增长。"
        ),
    },
]


def seed_agent_templates(session: Session) -> None:
    """初始化 AgentTemplate：若不存在则创建。"""
    for spec in AGENT_TEMPLATES:
        existing = session.scalar(select(AgentTemplate).where(AgentTemplate.name == spec["name"]))
        if existing:
            continue
        template = AgentTemplate(
            name=spec["name"],
            description=spec.get("description"),
            system_prompt=spec.get("system_prompt", ""),
            model=spec.get("model", "gpt-4"),
            default_tools=spec["default_tools"],
            default_workflows=spec.get("default_workflows", []),
            config_schema={},
            enabled=True,
        )
        session.add(template)
    session.commit()


def seed_auth_only(session: Session) -> None:
    """仅创建 Tenant 和 User，供 auth 登录使用；用于 init 阶段的 auth_db 和 project_db。"""
    seed_rbac_roles(session)
    existing_tenant = session.scalar(select(Tenant).where(Tenant.slug == "demo-enterprise"))
    if existing_tenant:
        return

    now = datetime.now(timezone.utc)
    tenant = Tenant(
        id=DEMO_TENANT_ID,
        name="Demo Enterprise",
        slug="demo-enterprise",
        status=TenantStatus.active,
        plan_name="growth",
        settings={
            "region": "us-east-1",
            "retention_days": 90,
            "features": ["agents", "tasks", "workflow-automation", "audit-logging"],
        },
    )
    owner = User(
        id=DEMO_OWNER_USER_ID,
        tenant=tenant,
        email="owner@demo-enterprise.ai",
        full_name="Platform Owner",
        hashed_password=pwd_context.hash("ChangeMe123!"),
        role=UserRole.admin,
        status=UserStatus.active,
        last_login_at=now,
    )
    manager = User(
        tenant=tenant,
        email="ops@demo-enterprise.ai",
        full_name="Operations Lead",
        hashed_password=pwd_context.hash("ChangeMe123!"),
        role=UserRole.manager,
        status=UserStatus.active,
    )
    operator = User(
        tenant=tenant,
        email="operator@demo-enterprise.ai",
        full_name="Platform Operator",
        hashed_password=pwd_context.hash("ChangeMe123!"),
        role=UserRole.operator,
        status=UserStatus.active,
    )
    session.add_all([tenant, owner, manager, operator])
    session.commit()


def seed_database(session: Session) -> None:
    seed_agent_templates(session)
    existing_tenant = session.scalar(select(Tenant).where(Tenant.slug == "demo-enterprise"))
    if existing_tenant:
        return

    now = datetime.now(timezone.utc)

    tenant = Tenant(
        name="Demo Enterprise",
        slug="demo-enterprise",
        status=TenantStatus.active,
        plan_name="growth",
        settings={
            "region": "us-east-1",
            "retention_days": 90,
            "features": ["agents", "tasks", "workflow-automation", "audit-logging"],
        },
    )

    owner = User(
        tenant=tenant,
        email="owner@demo-enterprise.ai",
        full_name="Platform Owner",
        hashed_password=pwd_context.hash("ChangeMe123!"),
        role=UserRole.admin,
        status=UserStatus.active,
        last_login_at=now,
    )
    manager = User(
        tenant=tenant,
        email="ops@demo-enterprise.ai",
        full_name="Operations Lead",
        hashed_password=pwd_context.hash("ChangeMe123!"),
        role=UserRole.manager,
        status=UserStatus.active,
    )
    operator = User(
        tenant=tenant,
        email="operator@demo-enterprise.ai",
        full_name="Platform Operator",
        hashed_password=pwd_context.hash("ChangeMe123!"),
        role=UserRole.operator,
        status=UserStatus.active,
    )

    project = Project(
        tenant=tenant,
        owner=owner,
        key="AIOPS",
        name="AI Operations Launch",
        description="Launch project for orchestrating AI employees across inbound operations.",
        status=ProjectStatus.active,
        metadata_json={
            "business_unit": "Revenue Operations",
            "timezone": "UTC",
            "default_priority": "high",
        },
    )

    research_agent = Agent(
        project=project,
        created_by=owner,
        name="Research Analyst",
        slug="research-analyst",
        role="seo_writer",
        role_title="Market Research Specialist",
        model="gpt-4.1",
        system_prompt="You analyze inbound requests, gather structured evidence, and produce concise summaries.",
        status=AgentStatus.active,
        max_concurrency=4,
        config={"temperature": 0.2, "max_output_tokens": 4000},
    )
    execution_agent = Agent(
        project=project,
        created_by=manager,
        name="Execution Coordinator",
        slug="execution-coordinator",
        role="software_engineer",
        role_title="Workflow Delivery Coordinator",
        model="gpt-4.1-mini",
        system_prompt="You break work into steps, call approved tools, and keep task execution on schedule.",
        status=AgentStatus.active,
        max_concurrency=8,
        config={"temperature": 0.1, "tool_mode": "strict"},
    )

    skills = [
        AgentSkill(
            agent=research_agent,
            name="Competitive Intelligence",
            category="analysis",
            proficiency_level=5,
            description="Collects and synthesizes market data for strategic decision-making.",
            is_core=True,
        ),
        AgentSkill(
            agent=research_agent,
            name="Document Summarization",
            category="language",
            proficiency_level=4,
            description="Produces structured briefs from long-form inputs.",
            is_core=True,
        ),
        AgentSkill(
            agent=execution_agent,
            name="Workflow Orchestration",
            category="operations",
            proficiency_level=5,
            description="Coordinates multi-step execution and handoffs.",
            is_core=True,
        ),
        AgentSkill(
            agent=execution_agent,
            name="Task Triage",
            category="operations",
            proficiency_level=4,
            description="Prioritizes queues and routes work to the right agent.",
            is_core=True,
        ),
    ]

    web_search_tool = Tool(
        project=project,
        name="Web Search",
        slug="web-search",
        tool_type=ToolType.integration,
        description="Queries external search providers for research tasks.",
        config={"provider": "serp", "rate_limit_per_minute": 60},
        is_enabled=True,
    )
    terminal_tool = Tool(
        project=project,
        name="Secure Terminal",
        slug="secure-terminal",
        tool_type=ToolType.terminal,
        description="Runs audited shell commands in isolated execution environments.",
        config={"sandbox": True, "allowed_profiles": ["readonly", "ops"]},
        is_enabled=True,
    )
    kb_tool = Tool(
        project=project,
        name="Knowledge Base",
        slug="knowledge-base",
        tool_type=ToolType.knowledge,
        description="Retrieves tenant-approved internal runbooks and SOPs.",
        config={"source": "pgvector", "namespace": "ops-playbooks"},
        is_enabled=True,
    )

    tool_links = [
        AgentToolLink(agent=research_agent, tool=web_search_tool, is_enabled=True, invocation_timeout_seconds=20),
        AgentToolLink(agent=research_agent, tool=kb_tool, is_enabled=True, invocation_timeout_seconds=15),
        AgentToolLink(agent=execution_agent, tool=terminal_tool, is_enabled=True, invocation_timeout_seconds=45),
        AgentToolLink(agent=execution_agent, tool=kb_tool, is_enabled=True, invocation_timeout_seconds=15),
    ]

    tool_permissions = [
        AgentToolPermission(agent=research_agent, tool_slug="seo"),
        AgentToolPermission(agent=execution_agent, tool_slug="wordpress"),
        AgentToolPermission(agent=execution_agent, tool_slug="facebook"),
    ]

    workflow = Workflow(
        project=project,
        name="Lead Qualification Workflow",
        slug="lead-qualification",
        version=1,
        status=WorkflowStatus.active,
        trigger_type=WorkflowTriggerType.manual,
        definition={
            "entrypoint": "capture-request",
            "success_state": "qualified",
            "failure_state": "needs-human-review",
        },
        published_at=now,
    )

    workflow_steps = [
        WorkflowStep(
            workflow=workflow,
            assigned_agent=research_agent,
            step_key="capture-request",
            name="Capture Request Context",
            step_type=WorkflowStepType.agent_task,
            sequence=1,
            retry_limit=1,
            timeout_seconds=300,
            config={"output_schema": "lead_context_v1"},
        ),
        WorkflowStep(
            workflow=workflow,
            assigned_agent=research_agent,
            tool=web_search_tool,
            step_key="market-enrichment",
            name="Market Enrichment",
            step_type=WorkflowStepType.tool_call,
            sequence=2,
            retry_limit=2,
            timeout_seconds=180,
            config={"query_template": "{{company_name}} competitors and market position"},
        ),
        WorkflowStep(
            workflow=workflow,
            assigned_agent=execution_agent,
            step_key="route-task",
            name="Route Follow-up Task",
            step_type=WorkflowStepType.agent_task,
            sequence=3,
            retry_limit=0,
            timeout_seconds=240,
            config={"next_queue": "sales-qualified"},
        ),
    ]

    workflow_links = [
        AgentWorkflowLink(agent=research_agent, workflow=workflow),
        AgentWorkflowLink(agent=execution_agent, workflow=workflow),
    ]

    writer_agent = Agent(
        project=project,
        name="Content Writer",
        slug="content-writer",
        role="content_creator",
        role_title="Article Writer",
        model="gpt-4.1-mini",
        system_prompt="You write clear, engaging articles based on the given topic.",
        status=AgentStatus.active,
        max_concurrency=4,
        config={"temperature": 0.7},
    )

    content_pipeline = Workflow(
        project=project,
        name="Content Pipeline",
        slug="content-pipeline",
        version=1,
        status=WorkflowStatus.active,
        trigger_type=WorkflowTriggerType.manual,
        definition={"entrypoint": "generate_article", "description": "generate_article → publish_wordpress → share_facebook"},
        published_at=now,
    )

    content_steps = [
        WorkflowStep(
            workflow=content_pipeline,
            assigned_agent=writer_agent,
            step_key="generate_article",
            name="Generate Article",
            step_type=WorkflowStepType.agent_task,
            sequence=1,
            next_step_key="publish_wordpress",
            retry_limit=1,
            timeout_seconds=300,
            config={
                "task_title": "Write blog post",
                "task_description": "Write an article based on the input topic.",
                "input_payload": {},
            },
        ),
        WorkflowStep(
            workflow=content_pipeline,
            step_key="publish_wordpress",
            name="Publish to WordPress",
            step_type=WorkflowStepType.tool_call,
            sequence=2,
            next_step_key="share_facebook",
            retry_limit=2,
            timeout_seconds=60,
            config={
                "tool_name": "wordpress",
                "action": "publish_post",
                "parameters": {"title": "", "content": "", "status": "publish"},
            },
        ),
        WorkflowStep(
            workflow=content_pipeline,
            step_key="share_facebook",
            name="Share on Facebook",
            step_type=WorkflowStepType.tool_call,
            sequence=3,
            retry_limit=2,
            timeout_seconds=60,
            config={
                "tool_name": "facebook",
                "action": "create_post",
                "parameters": {"page_id": "demo_page", "message": "", "link": ""},
            },
        ),
    ]

    content_workflow_links = [
        AgentWorkflowLink(agent=writer_agent, workflow=content_pipeline),
    ]

    # publish_article_workflow: fetch_content → seo_generate → publish_wordpress → log_result
    publish_article_workflow = Workflow(
        project=project,
        name="Publish Article Workflow",
        slug="publish_article_workflow",
        version=1,
        status=WorkflowStatus.active,
        trigger_type=WorkflowTriggerType.manual,
        definition={
            "steps": [
                {"tool": "fetch_content", "id": "fetch_content"},
                {"tool": "seo.generate_meta", "id": "seo_generate"},
                {"tool": "wordpress.publish_post", "id": "publish_wordpress"},
                {"tool": "log_result", "id": "log_result"},
            ],
        },
        published_at=now,
    )

    publish_article_steps = [
        WorkflowStep(
            workflow=publish_article_workflow,
            step_key="fetch_content",
            name="Fetch Content",
            step_type=WorkflowStepType.tool_call,
            sequence=1,
            next_step_key="seo_generate",
            retry_limit=2,
            timeout_seconds=60,
            config={
                "tool_name": "fetch_content",
                "action": "fetch",
                "parameters": {},
            },
        ),
        WorkflowStep(
            workflow=publish_article_workflow,
            step_key="seo_generate",
            name="SEO Generate Meta",
            step_type=WorkflowStepType.tool_call,
            sequence=2,
            next_step_key="publish_wordpress",
            retry_limit=2,
            timeout_seconds=120,
            config={
                "tool_name": "seo_generate_meta",
                "action": "generate",
                "parameters": {},
            },
        ),
        WorkflowStep(
            workflow=publish_article_workflow,
            step_key="publish_wordpress",
            name="Publish to WordPress",
            step_type=WorkflowStepType.tool_call,
            sequence=3,
            next_step_key="log_result",
            retry_limit=2,
            timeout_seconds=60,
            config={
                "tool_name": "wordpress_publish_post",
                "action": "publish",
                "parameters": {"status": "publish"},
            },
        ),
        WorkflowStep(
            workflow=publish_article_workflow,
            step_key="log_result",
            name="Log Result",
            step_type=WorkflowStepType.tool_call,
            sequence=4,
            next_step_key=None,
            retry_limit=0,
            timeout_seconds=30,
            config={
                "tool_name": "log_result",
                "action": "log",
                "parameters": {},
            },
        ),
    ]

    session.add_all(
        [
            writer_agent,
            content_pipeline,
            *content_steps,
            *content_workflow_links,
            publish_article_workflow,
            *publish_article_steps,
        ]
    )

    task = Task(
        project=project,
        agent=execution_agent,
        workflow=workflow,
        created_by=owner,
        title="Qualify ACME inbound lead",
        description="Review ACME request, enrich account context, and route the lead for human follow-up.",
        priority=TaskPriority.high,
        status=TaskStatus.running,
        attempt_count=1,
        max_attempts=3,
        due_at=now + timedelta(hours=6),
        started_at=now,
        input_payload={"lead_id": "lead_001", "source": "website", "company": "ACME"},
        output_payload={},
    )

    terminal = Terminal(
        project=project,
        agent=execution_agent,
        task=task,
        name="exec-coordinator-shell-01",
        status=TerminalStatus.connected,
        provider_ref="term_demo_001",
        capabilities={"shell": True, "python": True, "network_profile": "restricted"},
        last_seen_at=now,
    )

    team_memberships = [
        ProjectTeamMember(project=project, user=owner, role=UserRole.admin),
        ProjectTeamMember(project=project, user=manager, role=UserRole.manager),
        ProjectTeamMember(project=project, user=operator, role=UserRole.operator),
    ]

    session.add_all(
        [
            tenant,
            owner,
            manager,
            operator,
            project,
            research_agent,
            execution_agent,
            writer_agent,
            *skills,
            web_search_tool,
            terminal_tool,
            kb_tool,
            *tool_links,
            *tool_permissions,
            workflow,
            *workflow_steps,
            *workflow_links,
            content_pipeline,
            *content_steps,
            task,
            terminal,
            *team_memberships,
        ]
    )
    session.flush()

    audit_logs = [
        AuditLog(
            tenant=tenant,
            project=project,
            actor_user=owner,
            action=AuditAction.create,
            entity_type="project",
            entity_id=project.id,
            correlation_id="seed-project-create",
            user_agent="seed-script",
            payload={"message": "Seeded demo project"},
        ),
        AuditLog(
            tenant=tenant,
            project=project,
            actor_user=operator,
            action=AuditAction.assign,
            entity_type="task",
            entity_id=task.id,
            correlation_id="seed-task-assign",
            user_agent="seed-script",
            payload={"agent_slug": execution_agent.slug, "task_title": task.title},
        ),
    ]

    session.add_all(audit_logs)
    session.commit()
