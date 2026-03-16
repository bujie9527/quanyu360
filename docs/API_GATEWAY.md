# API Gateway

API Gateway 作为统一入口，负责 JWT 校验、限流、请求日志与服务路由。

## 架构

```
Client -> [Nginx] -> api-gateway -> 内部服务
                -> frontend (静态)
```

## 特性

| 特性 | 说明 |
|------|------|
| JWT 校验 | 非公开路径需有效 Bearer token |
| 限流 | SlowAPI，默认 100/min |
| 请求日志 | structlog JSON 输出 |
| 服务路由 | 按 path 前缀转发到对应服务 |

## 路由表

| 前缀 | 目标服务 |
|------|----------|
| /api/auth | auth-service:8001 |
| /api/projects | project-service:8002 |
| /api/agents | agent-service:8003 |
| /api/tasks | task-service:8004 |
| /api/workflows | workflow-service:8005 |
| /api/tools | tool-service:8006 |
| /api/admin | admin-service:8007 |
| /api/executions | workflow-engine:8100 |
| /api/runtime | agent-runtime:8200 |

## 公开路径（免 JWT）

- `/api/auth/login`
- `/api/auth/register`
- `/health/live`
- `/health/ready`

## 配置

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| JWT_SECRET_KEY | - | 与 auth-service 一致 |
| JWT_ALGORITHM | HS256 | 算法 |
| JWT_ISSUER | ai-workforce-platform | 签发者 |
| JWT_AUDIENCE | ai-workforce-platform-users | 受众 |
| JWT_ENABLED | true | 是否启用 JWT 校验 |
| RATE_LIMIT_DEFAULT | 100/minute | 默认限流 |
| *_SERVICE_URL | 见 config | 各服务地址 |

## 使用 Gateway 作为前端 API 入口

将前端环境变量指向 Gateway：

```
NEXT_PUBLIC_AUTH_SERVICE_URL=http://localhost:8300
NEXT_PUBLIC_PROJECT_SERVICE_URL=http://localhost:8300
NEXT_PUBLIC_AGENT_SERVICE_URL=http://localhost:8300
... (所有 API 指向 8300)
```

前端需将路径改为 `/api/auth/login`、`/api/projects` 等（加 `/api` 前缀）。或统一使用 `NEXT_PUBLIC_API_GATEWAY_URL` 作为 base，路径格式 `/api/{service}/{path}`。
