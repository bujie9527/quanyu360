#!/usr/bin/env bash
# 重启 AI Workforce Platform
# 用法: ./restart.sh [dev|prod]
# 等效于先执行 stop.sh，再执行 start.sh

set -e

MODE="${1:-prod}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[restart.sh] 正在重启 (模式: $MODE)..."
"$SCRIPT_DIR/stop.sh" "$MODE"
sleep 2
"$SCRIPT_DIR/start.sh" "$MODE"
echo "[restart.sh] 重启完成。"
