# 可持续交付门禁

本项目的测试、CI、迁移与监控能力说明。

## 1. 测试

### 后端 (pytest)
- 目录：`backend/tests/`
- 运行：`cd backend && PYTHONPATH=. pytest tests/unit/ -v`
- 或：`make test-backend`
- 依赖：`pytest`, `pytest-cov`, `pytest-asyncio`

### 前端 (Vitest)
- 目录：`frontend/__tests__/`
- 运行：`cd frontend && npm run test`
- 或：`make test-frontend`
- 依赖：`vitest`, `happy-dom`, `@testing-library/react`

## 2. CI (GitHub Actions)

工作流：`.github/workflows/ci.yml`

| Job | 说明 | 触发 |
|-----|------|------|
| backend-lint-test | 后端依赖安装、pytest 单元测试 | push/PR 到 main|master|develop |
| frontend-lint-test | 前端 lint、vitest、build | 同上 |
| migration-check | 校验 Alembic 迁移配置与历史 | 同上 |

## 3. 数据库迁移 (Alembic)

- 配置：`backend/alembic.ini`、`backend/alembic/env.py`
- 版本：`backend/alembic/versions/`
- 执行：`cd backend && DATABASE_URL=... alembic upgrade head`
- 或：`make migrate`（需设置 `DATABASE_URL`）
- 脚本：`backend/scripts/run_migration.sh`（供部署流程调用）

**与 Docker 的关系：**
- `backend-init` 使用 `create_all()` 初始化各服务 DB（auth、platform 等）
- Alembic 面向 **DATABASE_URL** 的增量迁移
- 生产部署建议：在 backend-init 完成后，由 deploy 流程调用 `run_migration.sh`

## 4. 监控与健康检查

- 健康端点：各后端服务提供 `/health/live`、`/health/ready`
- Smoke 检查：`sh tools/scripts/smoke-check.sh`（需服务已启动）
- 或：`make smoke`
- Prometheus：`task-service`、`agent-runtime` 提供 `/metrics`
- CI 门禁：lint、test、build 通过后方可合并；部署后建议执行 `make smoke` 做自检

## 5. 快速命令汇总

```bash
make test           # 后端+前端测试
make test-backend   # 仅后端
make test-frontend  # 仅前端
make lint-frontend  # 前端 lint
make build         # 前端构建
make smoke         # 健康检查
make migrate       # 执行迁移（需 DB）
make help          # 查看所有目标
```
