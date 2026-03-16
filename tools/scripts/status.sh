#!/usr/bin/env bash
# 查看 AI Workforce Platform 服务状态
# 用法: ./status.sh [dev|prod]

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
fi

export ENV_FILE
docker compose --env-file "$ENV_FILE" $COMPOSE_FILES ps
