#!/usr/bin/env sh

set -eu

ENV_FILE_PATH="${ENV_FILE_PATH:-.env.local.mac}"
COMPOSE_FILES="-f docker-compose.yml"

usage() {
  echo "用法: $0 [命令]"
  echo ""
  echo "命令:"
  echo "  up        （默认）构建并启动所有服务"
  echo "  restart   重启所有服务"
  echo "  restart --build   重建镜像并重启所有服务"
  echo "  down      停止并移除所有服务容器"
  echo "  -h, --help  显示此帮助"
  echo ""
  echo "示例:"
  echo "  sh tools/scripts/dev-up.sh           # 启动"
  echo "  sh tools/scripts/dev-up.sh restart  # 重启所有服务"
  echo "  sh tools/scripts/dev-up.sh restart --build  # 重建并重启"
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
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

MODE="${1:-up}"

case "$MODE" in
  up)
    echo "构建并启动本地开发栈..."
    ENV_FILE="$ENV_FILE_PATH" docker compose --env-file "$ENV_FILE_PATH" $COMPOSE_FILES up --build -d
    echo "本地环境启动完成。"
    ;;
  restart)
    if [ "${2:-}" = "--build" ]; then
      echo "重建镜像并重启所有服务..."
      ENV_FILE="$ENV_FILE_PATH" docker compose --env-file "$ENV_FILE_PATH" $COMPOSE_FILES up -d --build
    else
      echo "重启所有服务..."
      ENV_FILE="$ENV_FILE_PATH" docker compose --env-file "$ENV_FILE_PATH" $COMPOSE_FILES restart
    fi
    echo "所有服务重启完成。"
    ;;
  down)
    echo "停止并移除所有服务..."
    ENV_FILE="$ENV_FILE_PATH" docker compose --env-file "$ENV_FILE_PATH" $COMPOSE_FILES down
    echo "所有服务已停止。"
    ;;
  *)
    echo "未知命令: $MODE" >&2
    usage >&2
    exit 1
    ;;
esac

if [ "$MODE" != "down" ]; then
  echo ""
  echo "前端地址: http://localhost:3000"
echo "Auth 服务: http://localhost:8001"
echo "Project 服务: http://localhost:8002"
echo "Agent 服务: http://localhost:8003"
echo "Task 服务: http://localhost:8004"
echo "Workflow 服务: http://localhost:8005"
echo "Workflow Engine: http://localhost:8100"
echo "Agent Runtime: http://localhost:8200"
echo ""
echo "查看状态: docker compose --env-file $ENV_FILE_PATH ps"
echo "查看日志: docker compose --env-file $ENV_FILE_PATH logs -f"
echo "健康检查: sh tools/scripts/smoke-check.sh"
fi
