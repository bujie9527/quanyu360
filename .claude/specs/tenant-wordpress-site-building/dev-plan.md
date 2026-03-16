# 租户 WordPress 自动建站 - 开发计划

## Overview

实现租户批量创建 WordPress 自动建站任务，受平台建站配额限制，租户可从平台域名池选择域名，并实时查看 TaskRun + StepRun 执行情况。

## 数据模型设计

### 1. platform_domains 表

平台统一配置的域名池，每个域名已做好 DNS 解析和 SSL 配置。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| domain | String(255) | 域名，唯一 |
| api_base_url | String(512) | API 基础 URL（如 https://example.com） |
| ssl_enabled | Boolean | 是否已配置 SSL |
| status | Enum | available / assigned / inactive |
| created_at, updated_at | DateTime | 时间戳 |

**索引**: ix_platform_domains_status, ix_platform_domains_domain (unique)

### 2. wordpress_sites 表扩展

- 新增 `platform_domain_id` (UUID, FK platform_domains.id, nullable)，建站时从平台域名池选中后关联
- 保留原有 domain/api_url 等字段，建站完成后写入实际值

### 3. 配额扩展

- 在 Tenant.settings.quotas 中新增 `wordpress_sites_per_month`（建议命名，与 tasks_per_month 风格一致）
- QuotaService 按当月 WordPressSite 创建数统计

---

## API 设计

### 平台端 (admin-service)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /admin/platform_domains | 列表（分页、status 过滤） |
| POST | /admin/platform_domains | 创建 |
| PATCH | /admin/platform_domains/{id} | 更新 |
| DELETE | /admin/platform_domains/{id} | 删除 |
| GET | /admin/quotas/check?tenant_id=&resource=wordpress_sites_per_month | 扩展 resource 支持 |

### 租户端 (project-service / workflow-service)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/platform_domains/available | 租户可见可用域名列表（status=available） |
| POST | /api/site_building/batch | 创建批量建站任务（count, project_id, domain_ids[]） |
| GET | /api/task_runs | 扩展 project_id 过滤，仅返回该租户 project 下 workflow 的 TaskRun |
| GET | /api/task_runs/{id} | 租户鉴权：TaskRun.workflow.project.tenant_id == 当前租户 |
| GET | /api/quotas | 扩展返回 wordpress_sites_per_month |

---

## Task Breakdown

### Task 1: 平台域名数据模型与 CRUD API

- **ID**: task-1
- **type**: default
- **Description**: 新增 platform_domains 表、PlatformDomain 模型，实现 admin-service 的 CRUD 接口及租户可见的 GET /api/platform_domains/available
- **File Scope**: backend/common/app/models/platform.py, backend/alembic/versions/*, backend/services/admin-service/app/controllers/, app/services/, app/repositories/, backend/services/project-service/app/controllers/, frontend (若需管理 UI)
- **Dependencies**: None
- **Test Command**: `cd backend && pytest tests/ -v -k "platform_domain or platform_domains" --cov=common.app.models --cov=app --cov-report=term 2>/dev/null || pytest tests/ -v --cov-report=term`
- **Test Focus**: platform_domains CRUD、available 接口返回 status=available 的域名、权限隔离（租户仅见 available）

### Task 2: 建站配额 (wordpress_sites_per_month) 与校验

- **ID**: task-2
- **type**: default
- **Description**: 在 QuotaService 中新增 wordpress_sites_per_month 配额项，按当月 WordPressSite 创建数统计；扩展 quota_client.check_quota 支持该 resource；扩展 list_quotas/update_quotas 包含 wordpress_sites_per_month
- **File Scope**: backend/services/admin-service/app/services/quota_service.py, backend/common/app/quota_client.py, backend/services/admin-service/app/controllers/usage_controller.py
- **Dependencies**: None
- **Test Command**: `cd backend && pytest tests/ -v -k quota --cov=services/admin-service/app/services/quota_service --cov=common/app/quota_client --cov-report=term`
- **Test Focus**: wordpress_sites_per_month 统计逻辑、超限时 check 返回 allowed=False、list_quotas 包含新字段

### Task 3: 租户批量建站任务创建 API

- **ID**: task-3
- **type**: default
- **Description**: 实现 POST /api/site_building/batch：接收 count、project_id、domain_ids（从 platform_domains 选择）。校验 count ≤ 配额剩余；为每个域名创建 TaskTemplate 执行或批量触发 Workflow，生成对应 TaskRun；创建 WordPressSite 占位或在实际建站完成时写入
- **File Scope**: backend/services/project-service 或 workflow-service（新建 site_building 模块）, backend/services/task-service（若需创建 Task 记录）, tools/wordpress/*, workflow-engine
- **Dependencies**: task-1, task-2
- **Test Command**: `cd backend && pytest tests/ -v -k site_building --cov=app --cov-report=term`
- **Test Focus**: 配额校验拒绝超限请求、domain_ids 必须来自 available、成功创建 TaskRun、WordPressSite 正确关联 platform_domain_id

### Task 4: 租户 TaskRun/StepRun 查询 API（鉴权与过滤）

- **ID**: task-4
- **type**: default
- **Description**: 扩展 workflow-service 的 GET /task_runs 与 GET /task_runs/{id}：从请求上下文获取 tenant_id/project_id，仅返回 workflow.project.tenant_id == tenant_id 的 TaskRun；GET /task_runs/{id} 鉴权通过后才能返回 StepRuns
- **File Scope**: backend/services/workflow-service/app/controllers/task_runs_controller.py, app/repositories/task_run_repository.py, gateway（如需传递 tenant context）
- **Dependencies**: None
- **Test Command**: `cd backend && pytest tests/ -v -k task_run --cov=services/workflow-service/app --cov-report=term`
- **Test Focus**: 跨租户请求 404、同租户不同 project 过滤正确、StepRuns 仅在鉴权通过时返回

### Task 5: 前端 - 租户建站任务创建与实时执行查看 UI

- **ID**: task-5
- **type**: ui
- **Description**: 租户后台页面：① 建站任务创建表单（选择 project、输入数量、从可用域名多选）；显示当前 wordpress_sites_per_month 配额；② 任务执行列表与详情（TaskRun 列表、StepRun 实时展示，支持轮询或 SSE）
- **File Scope**: frontend/app/(dashboard)/, frontend/lib/api*.ts
- **Dependencies**: task-3, task-4
- **Test Command**: `cd frontend && npm run build && npm run lint`
- **Test Focus**: 表单校验（数量≤配额、必须选域名）、列表分页与刷新、StepRun 按时间顺序展示、错误态展示

---

## Acceptance Criteria

- [ ] platform_domains 表存在，支持 CRUD，租户可获取 available 域名列表
- [ ] wordpress_sites_per_month 配额生效，创建任务时校验不超限
- [ ] 租户可批量创建建站任务，数量与域名选择正确
- [ ] 租户可实时查看 TaskRun 及 StepRun 执行情况，且仅能查看本租户数据
- [ ] 平台可在 admin 端管理域名与租户配额
- [ ] 所有单元测试通过
- [ ] 代码覆盖率 ≥90%（相关模块）

---

## Technical Notes

- **Task vs TaskRun 关系**：Task 为平台任务实体（task-service）；TaskRun 为 Workflow 执行日志（workflow-service）。建站流程通过 TaskTemplate → Workflow 触发，TaskRun 记录每次执行，StepRun 记录每步。
- **域名占用**：建站任务创建时应将选中 domain 的 status 置为 assigned，建站完成或失败后根据策略释放或保留。
- **租户上下文**：Gateway 需在代理请求时注入 X-Tenant-Id 或从 JWT 解析 tenant_id，workflow-service 需支持从 Header/Context 读取并过滤。
- **实时更新**：前端可采用短轮询（如 3s）或 SSE；StepRun 在 workflow-engine 每步执行后写入，已有 append_step API。
