#!/usr/bin/env sh
# 502 诊断脚本：检查各服务状态并尝试恢复
# 用法: sh tools/scripts/diagnose.sh
# 在项目根目录执行

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

ENV_FILE="${ENV_FILE:-.env.production}"
[ -f .env ] && ENV_FILE=".env"
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"

echo "=== 502 诊断：检查服务状态 ==="
echo ""

echo "[1] 容器状态"
docker compose --env-file "$ENV_FILE" $COMPOSE_FILES ps 2>/dev/null || true

echo ""
echo "[2] 检查 nginx 能否访问 frontend"
if docker compose --env-file "$ENV_FILE" $COMPOSE_FILES exec -T nginx wget -qO- --timeout=3 http://frontend:3000 2>/dev/null | head -c 200; then
  echo ""
  echo "  ✓ frontend 可达"
else
  echo "  ✗ frontend 不可达（可能未运行或未就绪）"
fi

echo ""
echo "[3] 检查 nginx 能否访问 auth-service"
if docker compose --env-file "$ENV_FILE" $COMPOSE_FILES exec -T nginx wget -qO- --timeout=3 http://auth-service:8001/health/live 2>/dev/null; then
  echo "  ✓ auth-service 可达"
else
  echo "  ✗ auth-service 不可达"
fi

echo ""
echo "[4] frontend 最近日志（最后 20 行）"
docker compose --env-file "$ENV_FILE" $COMPOSE_FILES logs frontend --tail 20 2>/dev/null || true

echo ""
echo "=== 建议操作 ==="
echo "1. 若有容器 Exited：sh tools/scripts/restart.sh"
echo "2. 若 frontend 日志有错误：修复后 sh tools/scripts/dc.sh up -d --build frontend"
echo "3. 若仍 502：sh tools/scripts/dc.sh logs -f frontend 持续查看"
