#!/usr/bin/env sh

set -eu

ENV_FILE_PATH="${ENV_FILE_PATH:-.env.local.mac}"
COMPOSE_FILES="${COMPOSE_FILES:--f docker-compose.yml}"
SERVICE_NAME="frontend"
REBUILD="${REBUILD:-0}"

if [ "${1:-}" = "--build" ]; then
  REBUILD="1"
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker 未安装，或未加入 PATH。" >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker Desktop 未启动，请先启动后重试。" >&2
  exit 1
fi

if [ ! -f "$ENV_FILE_PATH" ]; then
  echo "环境文件不存在：$ENV_FILE_PATH" >&2
  echo "可先使用 .env.local.mac，或从 .env.example 复制生成。" >&2
  exit 1
fi

echo "使用环境文件：$ENV_FILE_PATH"
echo "校验 Docker Compose 配置..."
ENV_FILE="$ENV_FILE_PATH" docker compose --env-file "$ENV_FILE_PATH" $COMPOSE_FILES config >/dev/null

if [ "$REBUILD" = "1" ]; then
  echo "重建并启动前端服务..."
  ENV_FILE="$ENV_FILE_PATH" docker compose --env-file "$ENV_FILE_PATH" $COMPOSE_FILES up -d --build "$SERVICE_NAME"
else
  echo "重启前端服务..."
  ENV_FILE="$ENV_FILE_PATH" docker compose --env-file "$ENV_FILE_PATH" $COMPOSE_FILES restart "$SERVICE_NAME"
fi

echo "前端服务操作完成。"
echo "访问地址: http://localhost:3000"
echo "查看日志: docker compose --env-file $ENV_FILE_PATH $COMPOSE_FILES logs -f $SERVICE_NAME"
echo "重建启动: sh tools/scripts/restart-frontend.sh --build"
