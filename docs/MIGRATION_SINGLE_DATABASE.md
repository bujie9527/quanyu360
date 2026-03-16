# 多库迁移到单库设计文档

> **已完成**：本地全新环境已迁移为单库模式，所有服务共用 `DATABASE_URL`。

## 一、原架构概览（已废弃）

### 1.1 原多库架构

| 数据库 | 连接变量 | 使用方 |
|--------|----------|--------|
| platform | `PLATFORM_DATABASE_URL` | Alembic 迁移、seed_data.py、init_db.py |
| auth_db | `AUTH_DATABASE_URL` | auth-service、admin-service |
| project_db | `PROJECT_DATABASE_URL` | project-service |
| agent_db | `AGENT_DATABASE_URL` | agent-service |
| task_db | `TASK_DATABASE_URL` | task-service、task-worker |
| workflow_db | `WORKFLOW_DATABASE_URL` | workflow-service |

### 1.2 数据流

- **连接配置**：各服务通过 `DATABASE_URL` 环境变量获取连接串（docker-compose 中映射自 `*_DATABASE_URL`）
- **Session 工厂**：`create_session_factory(settings)` 使用 `settings.database_url`（来自 `DATABASE_URL`）
- **Schema**：`Base.metadata.create_all()` 在各库中创建**完整 schema**（所有模型表），多库实为**数据物理隔离**，非按领域分表
- **初始化**：`init_service_databases.py` 对 6 个库分别执行 `initialize_database` + 部分 seed

---

## 二、改造目标

- **单库**：所有后端服务共用同一个 PostgreSQL 数据库
- **单次初始化**：一次 `create_all` + 一次 seed
- **统一迁移**：Alembic 只作用于该库
- **配置收敛**：环境变量简化为一个 `DATABASE_URL`

---

## 三、改造点与步骤

### 阶段一：环境与基础设施

#### 3.1 PostgreSQL 初始化脚本

**文件**：`docker/postgres/init/01-init-databases.sql`

**当前**：创建 auth_db、project_db、agent_db、task_db、workflow_db

**改造**：删除或清空，不再创建多库。仅依赖 `POSTGRES_DB`（默认 `platform`）即可。

```sql
-- 单库模式：不创建额外数据库，使用 POSTGRES_DB（platform）
-- 原多库创建语句可移除
```

#### 3.2 环境变量

**文件**：`.env.example`、`.env.local.mac`、`.env.production.example`、`docker-compose.yml`

**改造**：

1. 新增统一变量 `DATABASE_URL`（或复用 `PLATFORM_DATABASE_URL` 作为主库）
2. 各服务统一使用该变量

```diff
# .env.example 示例
+ DATABASE_URL=postgresql+psycopg://platform_admin:change_me@postgres:5432/platform

- AUTH_DATABASE_URL=...
- PROJECT_DATABASE_URL=...
- AGENT_DATABASE_URL=...
- TASK_DATABASE_URL=...
- WORKFLOW_DATABASE_URL=...
```

保留 `PLATFORM_DATABASE_URL` 作为向后兼容别名亦可，单库时令其等于 `DATABASE_URL`。

---

### 阶段二：Docker Compose

**文件**：`docker-compose.yml`、`docker-compose.prod.yml`

**改造**：所有 backend 服务将 `DATABASE_URL` 指向同一变量。

```yaml
# 示例：统一使用 DATABASE_URL
auth-service:
  environment:
    DATABASE_URL: ${DATABASE_URL}  # 原 AUTH_DATABASE_URL

project-service:
  environment:
    DATABASE_URL: ${DATABASE_URL}  # 原 PROJECT_DATABASE_URL

# agent-service、task-service、task-worker、workflow-service、admin-service 同理
```

---

### 阶段三：数据库初始化脚本

**文件**：`backend/scripts/init_service_databases.py`

**当前**：遍历 6 个 `*_DATABASE_URL`，对每个库执行 `initialize_database` + 部分 seed。

**改造**：只初始化一个库，执行一次 schema + 一次 seed。

```python
# 改造后逻辑（伪代码）
DATABASE_URL_ENV = "DATABASE_URL"  # 或 PLATFORM_DATABASE_URL

def main():
    url = os.getenv(DATABASE_URL_ENV) or os.getenv("PLATFORM_DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL or PLATFORM_DATABASE_URL must be set.")
    
    engine = build_engine(url)
    initialize_database(engine)
    _ensure_tasks_team_id(engine)
    
    with Session(engine) as session:
        seed_auth_only(session)
```

**依赖注入**：各服务依赖的 `DATABASE_URL` 在环境变量中已统一，`ServiceSettings.database_url` 自动读取，无需改业务代码。

---

### 阶段四：Alembic 迁移

**文件**：`backend/alembic/env.py`、`backend/scripts/run_migration.sh`

**当前**：优先使用 `PLATFORM_DATABASE_URL`，其次 `DATABASE_URL`。

**改造**：单库场景下二者指向同一库即可，无需改 env.py。`run_migration.sh` 可改为依赖 `DATABASE_URL` 或保持现状。

---

### 阶段五：其他脚本

| 脚本 | 改造 |
|------|------|
| `backend/scripts/seed_data.py` | 使用 `DATABASE_URL` 或 `PLATFORM_DATABASE_URL`（已支持） |
| `backend/scripts/init_db.py` | 同上 |
| `backend/common/app/observability/health.py` | 已用 `DATABASE_URL`，无需改 |

---

### 阶段六：服务配置与依赖注入

**结论**：**无需改动**。

- 各服务通过 `ServiceSettings` 读取 `database_url`（对应 `DATABASE_URL`）
- `create_session_factory(settings)` 使用该 URL 创建引擎和 session
- Repository、Controller 依赖 `get_db_session()`，与具体 URL 解耦

只需在 docker-compose 中将各服务的 `DATABASE_URL` 统一即可。

---

## 四、迁移步骤清单（实施顺序）

| 序号 | 任务 | 文件/位置 |
|------|------|-----------|
| 1 | 修改 postgres init，移除多库创建 | `docker/postgres/init/01-init-databases.sql` |
| 2 | 新增/统一 `DATABASE_URL` | `.env.example`、`.env.local.mac` 等 |
| 3 | 修改 init_service_databases 为单库逻辑 | `backend/scripts/init_service_databases.py` |
| 4 | 修改 docker-compose 各服务 DATABASE_URL | `docker-compose.yml`、`docker-compose.prod.yml` |
| 5 | 本地验证：`docker compose down -v && docker compose up -d`，确认 `backend-init` 成功 | - |
| 6 | 验证各服务健康检查、登录、创建项目等核心流程 | - |

---

## 五、数据迁移（如已有生产数据）

若已有线上多库数据，需要一次性迁移到单库：

1. **导出**：对 auth_db、project_db、agent_db、task_db、workflow_db 分别 `pg_dump`
2. **合并**：将 dump 导入到单库时，注意：
   - 表已存在则 `INSERT ... ON CONFLICT` 或先清空再导入
   - 主键/外键冲突需处理（多库的 tenant、user 等 ID 可能重复）
3. **推荐**：开发/测试环境可直接 `docker compose down -v` 清空卷后按新架构重建；生产需单独编写迁移脚本

---

## 六、回滚方案

- 保留原 `*_DATABASE_URL` 的备份或注释
- 保留 `01-init-databases.sql` 原内容于版本控制
- 若需回退：恢复 init 脚本、恢复各服务 `DATABASE_URL` 映射、重新执行 `backend-init`

---

## 七、改造后的收益

- **Seed 一次**：tenant/user 等共享数据只需在一个库中维护
- **外键可用**：跨表引用在同一库内，可加 FK 约束
- **事务简单**：跨领域操作可在同一事务中完成
- **运维简化**：单库备份、监控、扩容策略统一
