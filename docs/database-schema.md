# Database Schema

## Scope

This document describes the shared PostgreSQL control-plane schema used by the AI Workforce Platform MVP.

## Core Entities

- `Tenant`: top-level tenant boundary for users, projects, and audit events.
- `User`: tenant-scoped operators with role-based access.
- `Project`: project workspace that owns agents, tools, tasks, workflows, and terminals.
- `Agent`: AI employee definition, model selection, instructions, and runtime configuration.
- `AgentSkill`: normalized list of agent skills with category and proficiency.
- `Tool`: project-scoped tool catalog entry.
- `AgentToolLink`: assignment bridge between agents and tools with enablement and timeout policy.
- `Workflow`: versioned workflow definition.
- `WorkflowStep`: ordered workflow step list with agent/tool routing.
- `Task`: execution unit routed to an agent and optionally linked to a workflow.
- `Terminal`: runtime terminal/session state for task execution.
- `AuditLog`: immutable event trail for security and operations.

## High-Value Indexes

- `users(tenant_id, email)` for tenant-scoped identity lookup.
- `projects(tenant_id, status)` for project dashboards.
- `agents(project_id, status)` for agent roster queries.
- `tasks(project_id, status, priority)` for operational boards.
- `workflow_steps(workflow_id, sequence)` for ordered workflow execution.
- `audit_logs(tenant_id, entity_type, entity_id)` for audit investigations.

## Migration Assets

- SQLAlchemy models: `backend/common/app/models/platform.py`
- Alembic config: `backend/alembic.ini`
- Alembic environment: `backend/alembic/env.py`
- Initial migration: `backend/alembic/versions/20260308_0001_create_platform_schema.py`
- Bootstrap script: `backend/scripts/init_db.py`
- Seed script: `backend/scripts/seed_data.py`
