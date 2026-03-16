#!/usr/bin/env bash
# 一键同步本地代码到服务器
# 用法: ./sync-to-server.sh [选项]
#   选项:
#     --with-env    同时同步 .env.production（默认不同步，避免覆盖服务器密钥）
#     --dry-run     仅预览，不实际传输

set -e

# 可配置项（通过环境变量覆盖）
SYNC_SERVER="${SYNC_SERVER:-43.165.195.151}"
SYNC_USER="${SYNC_USER:-ubuntu}"
SYNC_PORT="${SYNC_PORT:-22}"
SYNC_REMOTE_DIR="${SYNC_REMOTE_DIR:-/opt/ai-workforce}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

WITH_ENV=false
DRY_RUN=false

for arg in "$@"; do
  case $arg in
    --with-env)
      WITH_ENV=true
      ;;
    --dry-run)
      DRY_RUN=true
      ;;
    -h|--help)
      echo "用法: $0 [选项]"
      echo ""
      echo "选项:"
      echo "  --with-env    同时同步 .env.production 到服务器（慎用，可能覆盖服务器配置）"
      echo "  --dry-run     仅预览将要同步的文件，不实际传输"
      echo ""
      echo "环境变量:"
      echo "  SYNC_SERVER       服务器地址 (默认: 43.165.195.151)"
      echo "  SYNC_USER         用户名 (默认: ubuntu)"
      echo "  SYNC_PORT         SSH 端口 (默认: 22)"
      echo "  SYNC_REMOTE_DIR   远程目录 (默认: /opt/ai-workforce)"
      echo ""
      echo "示例:"
      echo "  $0                    # 同步代码（不同步 .env.production）"
      echo "  $0 --with-env        # 同步代码并包含 .env.production"
      echo "  SYNC_SERVER=1.2.3.4 $0   # 同步到指定服务器"
      exit 0
      ;;
  esac
done

cd "$PROJECT_ROOT"

# 排除列表（与 .dockerignore 对齐，并增加开发产物）
EXCLUDES=(
  --exclude='.git'
  --exclude='.gitignore'
  --exclude='.cursor'
  --exclude='.DS_Store'
  --exclude='.next'
  --exclude='**/.next'
  --exclude='node_modules'
  --exclude='**/node_modules'
  --exclude='__pycache__'
  --exclude='**/__pycache__'
  --exclude='.pytest_cache'
  --exclude='.mypy_cache'
  --exclude='.ruff_cache'
  --exclude='*.pyc'
  --exclude='*.pyo'
  --exclude='*.pyd'
  --exclude='.env'
  --exclude='.env.local'
  --exclude='.env.local.mac'
  --exclude='coverage'
  --exclude='dist'
  --exclude='build'
  --exclude='agent-transcripts'
  --exclude='*.log'
  --exclude='.venv'
  --exclude='venv'
)

if [ "$WITH_ENV" = false ]; then
  EXCLUDES+=(--exclude='.env.production')
fi

RSYNC_OPTS=(
  -avz
  --progress
  --delete
  --exclude-from='/dev/null'
  "${EXCLUDES[@]}"
)

if [ "$DRY_RUN" = true ]; then
  RSYNC_OPTS+=(--dry-run --verbose)
  echo "[sync] 预览模式，不会实际传输文件"
fi

DEST="${SYNC_USER}@${SYNC_SERVER}:${SYNC_REMOTE_DIR}"
echo "[sync] 源: $PROJECT_ROOT"
echo "[sync] 目标: $DEST"
echo ""

rsync "${RSYNC_OPTS[@]}" \
  --rsh="ssh -p ${SYNC_PORT} -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new" \
  ./ \
  "${DEST}/"

echo ""
echo "[sync] 同步完成。"

if [ "$DRY_RUN" = false ] && [ "$WITH_ENV" = false ]; then
  echo "[sync] 提示: 未同步 .env.production，服务器上的配置保持不变。"
  echo "[sync] 如需同步环境变量，请使用: $0 --with-env"
fi
