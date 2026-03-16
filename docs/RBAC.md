# Role Based Access Control (RBAC)

## Entities

| Entity | Description |
|--------|-------------|
| **Role** | Named role with slug (e.g. platform_admin, tenant_admin, operator, viewer) |
| **Permission** | Fine-grained permission: resource + action (e.g. projects:read, tenants:manage) |
| **User** | Links to Role via UserRoleAssignment |
| **UserRoleAssignment** | user_id, role_id, tenant_id (null = platform scope) |

## Built-in Roles

| Slug | Name | Scope |
|------|------|-------|
| platform_admin | Platform Admin | Platform-wide |
| tenant_admin | Tenant Admin | Per-tenant |
| operator | Operator | Per-tenant |
| viewer | Viewer | Per-tenant |

## Permissions

Permissions use `resource:action` format. Examples:
- `tenants:manage`, `tenants:read`
- `roles:manage`
- `users:manage`
- `projects:*`, `agents:*`, `tasks:*`, `workflows:*`

## APIs

| Method | Path | Description |
|--------|------|-------------|
| POST | /admin/roles | Create role |
| GET | /admin/roles | List roles |
| POST | /admin/users/{id}/roles | Assign role(s) to user |

### Assign roles to user

```json
POST /admin/users/{user_id}/roles
{
  "roles": [
    { "role_id": "uuid", "tenant_id": null },
    { "role_id": "uuid", "tenant_id": "tenant-uuid" }
  ]
}
```

- `tenant_id: null` = platform-scoped (e.g. platform_admin)
- `tenant_id: uuid` = tenant-scoped (e.g. tenant_admin for that tenant)

## Middleware

**RBACEnrichmentMiddleware** populates `request.state.effective_permissions` from JWT role (backward compat). Add after OptionalJWTMiddleware.

**require_permission(resource, action)** — FastAPI dependency to protect routes:

```python
from common.app.auth import require_permission

@router.get("/admin/tenants", dependencies=[Depends(require_permission("tenants", "read"))])
def list_tenants(): ...
```

## Database

RBAC tables live in auth_db (with users and tenants):
- `roles`
- `permissions`
- `role_permissions`
- `user_role_assignments`

Seed creates default roles and permissions on init.
