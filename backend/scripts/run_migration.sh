#!/usr/bin/env bash
# 对 PLATFORM_DATABASE_URL 执行 Alembic 迁移
# 用于部署流程或 CI 后的数据库升级
set -euo pipefail

cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-.}:$(pwd)"

if [ -z "${DATABASE_URL:-}" ] && [ -z "${PLATFORM_DATABASE_URL:-}" ]; then
  echo "DATABASE_URL or PLATFORM_DATABASE_URL not set, skipping migration."
  exit 0
fi

echo "Running alembic upgrade head..."
alembic upgrade head
echo "Migration completed."
