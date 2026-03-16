# AiWorkerCenter 可持续交付门禁
# Usage: make <target>

.PHONY: test test-backend test-frontend lint lint-backend lint-frontend build smoke migrate help

# 默认目标
help:
	@echo "可用目标:"
	@echo "  test          - 运行后端+前端测试"
	@echo "  test-backend  - 运行后端 pytest"
	@echo "  test-frontend - 运行前端 vitest"
	@echo "  lint          - 运行所有 lint"
	@echo "  lint-frontend - 前端 next lint"
	@echo "  build         - 构建前端"
	@echo "  smoke         - 健康检查（需服务已启动）"
	@echo "  migrate       - 执行 Alembic 迁移（需 PLATFORM_DATABASE_URL）"

test: test-backend test-frontend

test-backend:
	cd backend && PYTHONPATH=. python -m pytest tests/unit/ -v --tb=short 2>/dev/null || \
		(cd backend && pip install -q -r requirements.txt && PYTHONPATH=. python -m pytest tests/unit/ -v --tb=short)

test-frontend:
	cd frontend && npm run test

lint: lint-frontend
	@echo "Backend: add ruff/black when needed"

lint-frontend:
	cd frontend && npm run lint

build:
	cd frontend && npm run build

smoke:
	@bash tools/scripts/smoke-check.sh

migrate:
	cd backend && alembic upgrade head
