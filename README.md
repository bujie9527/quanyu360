# AI Workforce Platform MVP

这是一个面向 AI Workforce Platform 的生产级 MVP 项目骨架。系统允许用户创建 AI 员工、给它们分配任务，并通过工作流驱动整套执行链路。

## 技术栈

- 前端：Next.js 14、TypeScript、Tailwind CSS、shadcn/ui
- 后端：FastAPI、Python 3.11、SQLAlchemy、Pydantic
- 基础设施：PostgreSQL、Redis、Docker、Docker Compose

## 仓库结构

```text
.
├── frontend/
│   ├── app/
│   │   ├── (dashboard)/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── dashboard/
│   │   ├── layout/
│   │   └── ui/
│   ├── lib/
│   ├── public/
│   ├── components.json
│   ├── next.config.mjs
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── backend/
│   ├── common/
│   │   └── app/
│   │       ├── core/
│   │       ├── db/
│   │       ├── observability/
│   │       └── schemas/
│   ├── services/
│   │   ├── auth-service/
│   │   │   ├── app/
│   │   │   └── tests/
│   │   ├── project-service/
│   │   │   ├── app/
│   │   │   └── tests/
│   │   ├── agent-service/
│   │   │   ├── app/
│   │   │   └── tests/
│   │   ├── task-service/
│   │   │   ├── app/
│   │   │   └── tests/
│   │   └── workflow-service/
│   │       ├── app/
│   │       └── tests/
│   ├── requirements.txt
│   └── scripts/
│       ├── init_db.py
│       ├── init_service_databases.py
│       └── seed_data.py
├── agent-runtime/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   └── main.py
│   └── tests/
├── workflow-engine/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   └── main.py
│   └── tests/
├── tools/
│   └── scripts/
│       ├── deploy.sh
│       └── smoke-check.sh
├── docker/
│   ├── backend/
│   │   └── Dockerfile
│   ├── frontend/
│   │   └── Dockerfile
│   ├── nginx/
│   │   ├── Dockerfile
│   │   └── nginx.conf
│   └── postgres/
│       └── init/
│           └── 01-init-databases.sql
├── docs/
│   └── architecture.md
├── .dockerignore
├── .env.example
├── .env.production.example
├── .gitignore
├── docker-compose.yml
└── docker-compose.prod.yml
```

## 服务职责

- `auth-service`：身份认证、登录注册、未来的 JWT 与租户 RBAC
- `project-service`：项目空间与项目生命周期管理
- `agent-service`：AI 员工定义、角色和模型分配
- `task-service`：任务接入、任务分配与状态流转
- `workflow-service`：工作流模板 CRUD 与执行请求
- `workflow-engine`：工作流编排执行与事件分发
- `agent-runtime`：模型执行与工具调用运行时

## macOS 本地运行

如果你本地是 macOS，最简单、最稳定的方式是直接使用 Docker Desktop 跑整套系统。

### 前置要求

- 安装 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
- 确认 Docker 可用：

```bash
docker --version
docker compose version
```

- 建议给 Docker Desktop 至少分配：
  - CPU：4 核
  - 内存：8 GB
  - 磁盘：20 GB 以上

### 第一步：准备环境变量

在项目根目录执行：

```bash
cp .env.example .env
```

如果只是本地体验，`.env.example` 基本可以直接跑。  
如果你想接真实模型，请至少修改这些字段：

- `JWT_SECRET_KEY`
- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `OPENAI_API_KEY` 或 `CLAUDE_API_KEY`

如果你本机网络访问 Debian 软件源不稳定，也可以在 `/.env.local.mac` 里配置：

- `DEBIAN_MIRROR`
- `DEBIAN_SECURITY_MIRROR`
- `PIP_INDEX_URL`
- `PIP_EXTRA_INDEX_URL`
- `PIP_TRUSTED_HOST`

例如：

```bash
DEBIAN_MIRROR=https://mirrors.tuna.tsinghua.edu.cn/debian
DEBIAN_SECURITY_MIRROR=https://mirrors.tuna.tsinghua.edu.cn/debian-security
PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn
```

### 第二步：启动整套系统

```bash
docker compose up --build -d
```

首次启动会做这些事情：

- 拉取并构建前后端镜像
- 启动 `postgres` 和 `redis`
- 运行一次性初始化容器 `backend-init`
- 启动所有 API 服务
- 启动 `task-worker` 和 `workflow-engine-worker`
- 启动 `frontend`

### 第三步：检查容器状态

```bash
docker compose ps
```

查看实时日志：

```bash
docker compose logs -f
```

只看某个服务：

```bash
docker compose logs -f frontend
docker compose logs -f task-service
docker compose logs -f agent-runtime
```

### 第四步：访问本地地址

默认端口如下：

- 前端：`http://localhost:3000`
- `auth-service`：`http://localhost:8001`
- `project-service`：`http://localhost:8002`
- `agent-service`：`http://localhost:8003`
- `task-service`：`http://localhost:8004`
- `workflow-service`：`http://localhost:8005`
- `workflow-engine`：`http://localhost:8100`
- `agent-runtime`：`http://localhost:8200`
- PostgreSQL：`localhost:5432`
- Redis：`localhost:6379`

### 第五步：做健康检查

启动完成后执行：

```bash
sh tools/scripts/smoke-check.sh
```

如果全部正常，你会看到所有接口检查通过。

### 第六步：登录（Trial-ready 鉴权）

平台已接入统一鉴权与租户上下文，支持 trial-ready 闭环：

1. 访问 `http://localhost:3000/login`，使用演示账号登录：
   - 租户：`demo-enterprise`
   - 邮箱：`owner@demo-enterprise.ai`
   - 密码：`ChangeMe123!`（seed 默认）

2. 登录后，前端会自动携带 JWT，项目 / 智能员工 / 任务等 API 将按租户隔离。

3. 环境变量 `AUTH_REQUIRED=false`（默认）时，未登录仍可访问；设为 `true` 则需登录后才能操作。

4. Task Worker 调用 Agent Runtime 时会传递 `tenant_id` 等元数据，形成端到端租户上下文。

### 常见问题

如果 `3000`、`5432`、`6379` 或 `8001-8200` 端口被占用：

```bash
lsof -nP -iTCP:3000 | grep LISTEN
lsof -nP -iTCP:5432 | grep LISTEN
```

如果 Docker Desktop 资源太小，常见现象包括：

- 构建很慢
- 某些服务反复重启
- 前端 build 失败
- PostgreSQL 或 Redis 启动慢

这时先提高 Docker Desktop 的 CPU 和内存配额，再重新执行：

```bash
docker compose down
docker compose up --build -d
```

### 停止与清理

停止整套系统：

```bash
docker compose down
```

连同卷一起清理：

```bash
docker compose down -v
```

注意：`-v` 会删除 PostgreSQL 和 Redis 的持久化数据。

## Docker Compose

根目录下的 `docker-compose.yml` 会启动：

- `postgres`，并为各 API 服务准备独立逻辑数据库
- `redis`，带密码保护和 AOF 持久化
- 一次性初始化容器 `backend-init`，用于初始化所有带 schema 的数据库
- 5 个 FastAPI 领域服务
- 专门负责 Redis 任务消费的 `task-worker`
- 1 个 `agent-runtime`
- 1 个工作流执行 API，以及对应的 `workflow-engine-worker`
- 1 个 Next.js 前端

启动整套开发/本地环境：

```bash
cp .env.example .env
docker compose up --build -d
```

当前 Compose 已经不是“只适合开发”的最简版本，而是偏部署导向的设计：

- Python 和 Node 镜像默认以非 root 用户运行
- 前端构建时会注入 `NEXT_PUBLIC_*`，确保浏览器端访问正确的 API 地址
- 所有依赖数据库的服务会等待 `backend-init` 完成
- `task-service` 和 `workflow-engine` 的 worker 以独立容器部署
- 所有 HTTP 服务都有健康检查
- PostgreSQL 和 Redis 都配置了持久化卷

### 生产 Overlay

仓库还提供了 `docker-compose.prod.yml`，它会：

- 取消内部 API、PostgreSQL、Redis 对宿主机的直接暴露
- 引入 `nginx` 作为统一公网入口
- 通过路径路由把浏览器请求转发到前端和后端服务
- 支持前端通过 `/api/projects`、`/api/tasks`、`/api/runtime`、`/api/executions` 等路径访问服务

以生产风格启动：

```bash
cp .env.production.example .env.production
sh tools/scripts/deploy.sh
```

## 环境变量

主要环境变量位于 `.env.example`。

- 平台级：`COMPOSE_PROJECT_NAME`、`ENVIRONMENT`、`CORS_ORIGINS`
- 端口和并发：`POSTGRES_PUBLISHED_PORT`、`REDIS_PUBLISHED_PORT`、`FRONTEND_PUBLISHED_PORT`、`API_WEB_CONCURRENCY`、`ENGINE_WEB_CONCURRENCY`、`RUNTIME_WEB_CONCURRENCY`
- Debian 构建镜像源：`DEBIAN_MIRROR`、`DEBIAN_SECURITY_MIRROR`
- Python 包镜像源：`PIP_INDEX_URL`、`PIP_EXTRA_INDEX_URL`、`PIP_TRUSTED_HOST`
- 数据库：`POSTGRES_*`、`DATABASE_URL`
- 缓存与消息：`REDIS_*`
- 鉴权：`JWT_SECRET_KEY`、`JWT_ALGORITHM`、`JWT_ISSUER`、`JWT_AUDIENCE`、`ACCESS_TOKEN_EXPIRE_MINUTES`
- 服务级：`*_SERVICE_NAME`、`*_SERVICE_PORT`、`DATABASE_URL`、`*_REDIS_URL`
- 任务执行：`TASK_QUEUE_NAME`、`TASK_WORKER_BLOCK_SECONDS`、`TASK_DEFAULT_MAX_ATTEMPTS`
- 工作流执行：`WORKFLOW_ENGINE_URL`、`EXECUTION_QUEUE_NAME`、`EXECUTION_STATE_PREFIX`、`EXECUTION_INDEX_KEY`、`EXECUTION_WORKER_BLOCK_SECONDS`、`MAX_DELAY_SECONDS`
- 执行层：`WORKFLOW_ENGINE_*`、`AGENT_RUNTIME_*`
- 工具插件：`ENABLED_TOOL_PLUGINS`
- Agent Runtime LLM：`MEMORY_KEY_PREFIX`、`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`CLAUDE_API_KEY`、`CLAUDE_BASE_URL`、`LOCAL_MODEL_BASE_URL`、`LOCAL_MODEL_API_KEY`、`LLM_REQUEST_TIMEOUT_SECONDS`
- 前端公开地址：`NEXT_PUBLIC_*`
- 生产边缘入口：`NGINX_HTTP_PORT`

## PostgreSQL Schema

当前 MVP 已经包含一套面向生产的 PostgreSQL 控制平面 schema，核心实体包括：

- `Tenant`
- `User`
- `Project`
- `Agent`
- `AgentSkill`
- `Task`
- `Workflow`
- `WorkflowStep`
- `Terminal`
- `Tool`
- `AuditLog`

SQLAlchemy 模型位于 `backend/common/app/models/platform.py`。

### 迁移流程

在 `backend/` 目录执行：

```bash
export DATABASE_URL="postgresql+psycopg://platform_admin:change_me@localhost:5432/platform"
alembic upgrade head
python scripts/seed_data.py
```

如果本地只是快速初始化，也可以不走 Alembic，直接：

```bash
export DATABASE_URL="postgresql+psycopg://platform_admin:change_me@localhost:5432/platform"
python scripts/init_db.py
python scripts/seed_data.py
```

### 数据库设计说明

- 所有主实体都使用 UUID 主键，并带有 `created_at` 和 `updated_at`
- 多租户隔离从 `Tenant` 开始，向 `User` 和 `Project` 传播
- 工作执行主链路由 `Task`、`Workflow`、`WorkflowStep`、`Terminal` 建模
- `AgentToolLink` 作为支持型关联模型存在，用于承载 agent 级别的工具启用与调用限制
- 高频访问路径上已经补了复合索引，例如租户用户查询、项目任务面板、工作流步骤排序、审计过滤和运行时分配

## 前端说明

前端是一个基于 Next.js 14 App Router 的应用，具备：

- Tailwind CSS 配置
- 位于 `frontend/components/ui/` 的 shadcn/ui 风格基础组件
- 面向运营后台的控制台界面
- 当后端不可用时仍可优雅降级的服务健康展示
- 为 Docker 生产部署启用的 standalone 输出
- 基于 Chart.js 的监控与分析图表

## 后端说明

后端采用可独立部署的多服务拆分，而不是单体应用。跨服务的公共能力位于 `backend/common/`，包括：

- 服务配置
- SQLAlchemy Base / Session 工具
- 结构化日志
- 健康检查响应 schema

当前每个后端服务都至少暴露：

- `/health/live`
- `/health/ready`
- 一组基础的 `/api/v1/...` 领域接口

`auth-service` 额外提供：

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

认证系统说明：

- 基于 `passlib` 的 bcrypt 密码哈希
- 带 issuer 和 audience 校验的 JWT
- 租户感知的注册流程
- 基于依赖注入的 `admin`、`manager`、`operator` RBAC 校验

`task-service` 额外提供：

- `POST /tasks`
- `GET /tasks`
- `GET /tasks/{id}`
- `POST /tasks/{id}/run`
- `POST /tasks/{id}/cancel`

任务执行说明：

- 基于 Redis 的任务队列
- worker 入口位于 `backend/services/task-service/app/worker.py`
- 重试元数据持久化在 `tasks.attempt_count`、`tasks.max_attempts`、`tasks.last_error`

`workflow-service` 额外提供：

- `POST /workflows`
- `GET /workflows`
- `GET /workflows/{id}`
- `PUT /workflows/{id}`
- `DELETE /workflows/{id}`
- `POST /workflows/{id}/execute`

`workflow-engine` 额外提供：

- `POST /api/v1/executions`
- `GET /api/v1/executions`
- `GET /api/v1/executions/{id}`

工作流引擎说明：

- 工作流定义在 `workflow-service` 中维护
- 工作流执行状态和队列由 `workflow-engine` 基于 Redis 管理
- 支持的步骤类型包括：`agent_task`、`tool_call`、`condition`、`delay`
- 步骤流转优先使用显式 `next_step`，否则退回到序号顺序

`agent-runtime` 内置插件式工具系统：

- 支持动态工具注册表
- MVP 插件：`WordPressTool`、`FacebookTool`
- WordPress 动作：`publish_post`、`update_post`
- Facebook 动作：`create_post`、`comment_post`
- Agent 可以通过 `tool_name`、`action`、`parameters` 动态调用工具

`agent-runtime` 同时内置完整 AI 执行流水线：

- `Task -> Planner -> Tool Execution -> Result`
- `AgentRunner` 负责完整运行生命周期编排
- `ToolExecutor` 负责动态工具执行
- `RuntimeMemory` 负责执行记忆采集，并可持久化到 Redis
- LLM 抽象层支持 OpenAI、Claude、本地模型
- 如果未配置真实模型凭据，运行时会退回到确定性规划逻辑，保证开发环境仍可跑通

监控与分析说明：

- `task-service` 暴露 `GET /metrics` 和 `GET /tasks/analytics`
- `agent-runtime` 暴露 `GET /metrics` 和 `GET /api/v1/analytics/summary`
- Dashboard 使用 Chart.js 展示任务吞吐、成功率、执行时间和 token 使用情况

## 运维脚本

整套服务启动后，可执行：

```bash
sh tools/scripts/smoke-check.sh
```

它会对各服务以及前端做基础健康检查。

如果你跑的是带代理入口的生产风格部署，可执行：

```bash
SMOKE_CHECK_MODE=proxy SMOKE_CHECK_BASE_URL=http://localhost sh tools/scripts/smoke-check.sh
```

## 生产 Docker 说明

如果是偏生产风格的容器部署，建议这样做：

- 从 `.env.example` 复制出 `.env`，并替换所有占位密钥
- 如果走代理入口部署，从 `.env.production.example` 复制出 `.env.production`
- 把 `NEXT_PUBLIC_*` 配成浏览器真实可访问的公网地址
- 确保 PostgreSQL 和 Redis 使用持久化卷
- 按机器 CPU / 内存调整 `API_WEB_CONCURRENCY`、`ENGINE_WEB_CONCURRENCY`、`RUNTIME_WEB_CONCURRENCY`
- 必须同时部署 `task-worker` 和 `workflow-engine-worker`，否则队列中的任务不会真正执行
- 优先通过 `nginx` 边缘容器作为统一入口，而不是把所有内部服务直接暴露到公网

## 架构文档

更完整的服务边界、拓扑和运行流程说明，请查看 `docs/architecture.md`。
