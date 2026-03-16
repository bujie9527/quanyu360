# Multi-Tenant Architecture

## Overview

The platform uses a **tenant-per-row** isolation model where Tenant, User, and Project (and related entities) include `tenant_id` for data isolation.

## Entities and tenant_id

| Entity | tenant_id | Notes |
|--------|-----------|-------|
| **Tenant** | — | Root entity; no tenant_id |
| **User** | ✅ | FK to tenants.id |
| **Project** | ✅ | FK to tenants.id |
| Agent | via Project | Belongs to project → project.tenant_id |
| Task | via Project | Belongs to project → project.tenant_id |
| Workflow | via Project | Belongs to project → project.tenant_id |
| Asset | ✅ | Direct tenant_id |
| AuditLog | ✅ | Direct tenant_id |

## Tenant Context Middleware

`OptionalJWTMiddleware` parses `Authorization: Bearer <token>` and populates `request.state.token_claims`. The JWT includes:

- `tenant_id` — Current tenant
- `sub` — User ID
- `tenant_slug`
- `email`
- `role`

`get_tenant_context(request)` returns a `TenantContext` when a valid token is present. Controllers use:

- `get_tenant_context_dep` — Optional; returns `None` if no token
- `get_tenant_context_required` — Raises 401 if no token

Example (project-service):

```python
ctx: TenantContext | None = Depends(get_tenant_context_dep)
effective_tenant = ctx.tenant_id if ctx else tenant_id  # from query
```

## Data Isolation

Services enforce tenant isolation by:

1. Filtering list queries with `tenant_id` when context is present
2. Checking `project.tenant_id == ctx.tenant_id` before returning or updating
3. Requiring tenant context for sensitive operations (e.g. asset upload)

Repositories receive `tenant_id` and apply it in `WHERE` clauses.

## Admin API

### Tenant Management
| Method | Path | Description |
|--------|------|-------------|
| POST | /admin/tenants | Create tenant |
| GET | /admin/tenants | List tenants (paginated) |
| GET | /admin/tenants/{id} | Get tenant by ID |

### Platform Dashboard
| Method | Path | Description |
|--------|------|-------------|
| GET | /admin/dashboard | Totals (users, tenants, projects, agents, tasks) + system health |
| GET | /admin/users | List users |
| GET | /admin/projects | List projects |
| GET | /admin/agents | List agents |
| GET | /admin/tasks | List tasks |

Via API Gateway: `/api/admin/*`

## Database

- **单库模式**：所有服务共用 `DATABASE_URL` 指向的 PostgreSQL 数据库（platform）。
- Tenants、Users 及 Project、Agent、Task、Workflow 等实体在同一库中，通过 `tenant_id` 隔离。
