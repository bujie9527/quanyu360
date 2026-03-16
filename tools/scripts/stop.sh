#!/usr/bin/env bash
# 停止 AI Workforce Platform
# 用法: ./stop.sh [dev|prod]

set -e

MODE="${1:-prod}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

case "$MODE" in
  dev)
    ENV_FILE="${ENV_FILE:-.env}"
    COMPOSE_FILES="-f docker-compose.yml"
    ;;
  prod)
    ENV_FILE="${ENV_FILE:-.env.production}"
    COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
    ;;
  *)
    echo "用法: $0 [dev|prod]" >&2
    exit 1
    ;;
esac

if [ ! -f "$ENV_FILE" ]; then
  ENV_FILE=".env"
  if [ ! -f "$ENV_FILE" ]; then
    echo "警告: 未找到环境文件，使用默认配置停止。" >&2
  fi
fi

echo "[stop.sh] 正在停止服务..."
export ENV_FILE
docker compose --env-file "$ENV_FILE" $COMPOSE_FILES down

echo "[stop.sh] 已停止所有服务。"
