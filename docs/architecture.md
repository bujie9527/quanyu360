# AI Workforce Platform Architecture

## Goals

This MVP is structured as a production-grade multi-service platform for managing AI employees, their tasks, and the workflows that coordinate them. The architecture favors clear service boundaries, isolated data stores, and operational readiness over early monolith convenience.

## Bounded Contexts

- `auth-service`: identity, sessions, JWT issuance, tenant membership, RBAC.
- `project-service`: workspaces, projects, ownership, project metadata.
- `agent-service`: AI employee definitions, models, instructions, tool access policies.
- `task-service`: task queue, assignment, lifecycle state, audit trail.
- `workflow-service`: workflow templates, triggers, step definitions, approval topology.
- `workflow-engine`: execution orchestrator, workflow dispatch, event-driven state transitions.
- `agent-runtime`: runtime execution layer for model invocation, tool calling, and artifact return.

## Runtime Topology

```text
Next.js Frontend
    |
    +--> auth-service
    +--> project-service
    +--> agent-service
    +--> task-service
    +--> workflow-service
                |
                +--> workflow-engine --> Redis streams
                                      |
                                      +--> agent-runtime

PostgreSQL
    +--> auth_db
    +--> project_db
    +--> agent_db
    +--> task_db
    +--> workflow_db

Redis
    +--> cache, transient coordination, workflow events, runtime signaling
```

## Data and Control Flow

1. A user authenticates through `auth-service`.
2. The frontend creates or opens a project using `project-service`.
3. AI employees are provisioned in `agent-service`, including role, default model, and future tool policies.
4. Work is created in `task-service` and linked to a project and agent assignment.
5. Reusable orchestration templates live in `workflow-service`.
6. When execution is requested, `workflow-service` delegates to `workflow-engine`.
7. `workflow-engine` publishes and tracks execution state through Redis-backed coordination.
8. `agent-runtime` performs execution and returns structured results for task updates and downstream workflow transitions.

## Repository Layout Principles

- `frontend/` contains the Next.js operator console.
- `backend/common/` contains reusable FastAPI configuration, database setup, schemas, and observability helpers.
- `backend/services/*` contains one deployable API service per bounded context.
- `workflow-engine/` and `agent-runtime/` are independent execution-plane services.
- `docker/` contains reusable image definitions and database bootstrap assets.
- `tools/` contains operational and developer scripts.
- `docs/` contains architectural decisions and onboarding documentation.

## Production Readiness Notes

- Each backend service has a dedicated database URL and isolated Redis logical database.
- Docker healthchecks are defined for infrastructure and application services.
- The frontend uses standalone Next.js output for lean production containers.
- Shared FastAPI code lives in `backend/common/` to reduce divergence without collapsing service boundaries.
- The current endpoints are intentionally skeletal, but the deployment topology, runtime split, and service contracts are ready for domain implementation.
