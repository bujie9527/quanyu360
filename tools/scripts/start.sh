#!/usr/bin/env bash
# 启动 AI Workforce Platform 生产环境
# 用法: ./start.sh [dev|prod]
#   dev  - 开发模式，使用 docker-compose.yml
#   prod - 生产模式，使用 docker-compose.yml + docker-compose.prod.yml（默认）

set -e

MODE="${1:-prod}"
# 使用 $0 以兼容 sh/bash；从 tools/scripts/ 到项目根目录需返回两级
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

case "$MODE" in
  dev)
    ENV_FILE="${ENV_FILE:-.env}"
    COMPOSE_FILES="-f docker-compose.yml"
    echo "[start.sh] 开发模式: 使用 $ENV_FILE"
    ;;
  prod)
    ENV_FILE="${ENV_FILE:-.env.production}"
    COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
    echo "[start.sh] 生产模式: 使用 $ENV_FILE"
    ;;
  *)
    echo "用法: $0 [dev|prod]" >&2
    exit 1
    ;;
esac

if [ ! -f "$ENV_FILE" ]; then
  echo "错误: 环境文件不存在: $ENV_FILE" >&2
  echo "请从 .env.example 或 .env.production.example 复制并修改。" >&2
  exit 1
fi

# 生产模式：创建 .env 符号链接，使 docker compose 直接运行（如 ps/logs）时也能读取配置
if [ "$MODE" = "prod" ]; then
  ln -sf .env.production .env
  echo "[start.sh] 已创建 .env -> .env.production"
fi

echo "[start.sh] 正在启动服务..."
export ENV_FILE
docker compose --env-file "$ENV_FILE" $COMPOSE_FILES up -d --build

echo "[start.sh] 启动完成。"
echo "  查看状态: sh tools/scripts/status.sh  或  sh tools/scripts/dc.sh ps"
echo "  查看日志: sh tools/scripts/dc.sh logs -f"
