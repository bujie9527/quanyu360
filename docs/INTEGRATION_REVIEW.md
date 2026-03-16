# 平台集成与未实现接口审查报告

## 一、本次已完成的集成

### 1. 平台管理后台 (Admin)

| 功能 | 状态 | 说明 |
|------|------|------|
| 任务管理页面 | ✅ 新增 | `/admin/tasks` - 调用 `listAdminTasks`，展示跨项目任务列表 |
| 任务管理导航 | ✅ 新增 | 侧边栏和 pageMeta 已添加 |
| 管理概览快捷入口 | ✅ 完善 | 新增「任务管理」「审计日志」快捷链接 |
| 租户详情 | ✅ 新增 | 租户列表支持点击查看详情，调用 `getTenantDetail` |

### 2. 租户管理后台 (Tenant Dashboard)

| 功能 | 状态 | 说明 |
|------|------|------|
| 可用工具数 | ✅ 新增 | 智能员工页展示工具数量，调用 `listTools` |
| 工具 API | ✅ 新增 | `api.ts` 中新增 `listTools()`，对接 `/api/tools` |

### 3. API 层

| API | 文件 | 说明 |
|-----|------|------|
| `getTenantDetail(tenantId)` | api-admin.ts | 调用 `GET /admin/tenants/{id}` |
| `listTools()` | api.ts | 调用 `GET /api/tools`，失败时返回空数组 |

---

## 二、后端已实现但前端尚未集成的接口

| 后端接口 | 服务 | 建议集成位置 |
|----------|------|--------------|
| `GET /tenants/{id}` | admin-service | ✅ 已集成（租户详情） |
| `GET /admin/tasks` | admin-service | ✅ 已集成（任务管理页） |
| `GET /projects/{id}` | project-service | 项目详情页、编辑项目 |
| `PUT /projects/{id}` | project-service | 项目编辑 |
| `DELETE /projects/{id}` | project-service | 项目删除 |
| `POST /projects/{id}/assets/upload` | project-service | 资产上传 |
| `POST/GET/PUT/DELETE /projects/{id}/agent-teams/*` | project-service | Agent 团队 CRUD |
| `GET /agents/{id}` | agent-service | Agent 详情、编辑 |
| `PUT /agents/{id}` | agent-service | Agent 编辑 |
| `DELETE /agents/{id}` | agent-service | Agent 删除 |
| `GET /workflows/{id}` | workflow-service | 工作流详情（非 builder 格式） |
| `PUT /workflows/{id}` | workflow-service | 工作流更新 |
| `DELETE /workflows/{id}` | workflow-service | 工作流删除 |
| `POST /admin/roles`, `GET /admin/roles` | admin-service | 角色管理（无 UI） |
| `POST /users/{id}/roles` | admin-service | 用户角色分配 |
| `POST /auth/register` | auth-service | 注册（无前端） |
| `GET /auth/me` | auth-service | 当前用户（topbar/auth 可能已用） |

---

## 三、Stub / 占位实现

| 位置 | 说明 |
|------|------|
| `tool-service` | `ToolService.list_tools()` 固定返回 `items=[]`，需接入实际工具注册表 |
| `admin/settings` 页面 | 占位「敬请期待」，需实现平台配置 UI |

---

## 四、导航与路由一览

### Admin 侧边栏

- 管理概览 `/admin`
- 租户管理 `/admin/tenants`
- 用户管理 `/admin/users`
- 项目管理 `/admin/projects`
- Agent 管理 `/admin/agents`
- 任务管理 `/admin/tasks`（新增）
- 审计日志 `/admin/audit`
- 系统设置 `/admin/settings`

### Tenant 侧边栏

- 工作台 `/dashboard`
- 数据分析 `/analytics`
- 项目空间 `/projects`
- 智能员工 `/agents`
- 任务中心 `/tasks`
- 流程编排 `/workflow-builder`
- 执行结果 `/results`

---

## 五、后续建议

1. **项目/Agent/工作流 CRUD**：在租户侧增加详情、编辑、删除入口。
2. **工具服务**：实现 tool-service 的真实工具列表，或改为从 agent-runtime 获取。
3. **系统设置**：实现 admin/settings 页面，接入平台配置。
4. **角色管理**：如需 RBAC 精细化，可新增角色与权限管理页。
