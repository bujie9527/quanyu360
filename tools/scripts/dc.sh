#!/usr/bin/env sh
# Docker Compose 便捷封装（使用生产配置）
# 用法: sh tools/scripts/dc.sh <子命令> [参数...]
# 示例: sh tools/scripts/dc.sh ps
#       sh tools/scripts/dc.sh logs -f nginx

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"

if [ ! -f "$ENV_FILE" ]; then
  if [ -f .env ]; then
    ENV_FILE=".env"
  else
    echo "错误: 未找到 $ENV_FILE 或 .env" >&2
    exit 1
  fi
fi

exec docker compose --env-file "$ENV_FILE" $COMPOSE_FILES "$@"
