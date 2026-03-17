#!/usr/bin/env bash
# Sync local code to server (dev/migration only; not for production release)
# Usage: ./sync-to-server.sh [--with-env] [--dry-run]

set -e

SYNC_SERVER="${SYNC_SERVER:-43.165.195.151}"
SYNC_USER="${SYNC_USER:-ubuntu}"
SYNC_PORT="${SYNC_PORT:-22}"
SYNC_REMOTE_DIR="${SYNC_REMOTE_DIR:-/opt/ai-workforce}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

WITH_ENV=false
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --with-env)
      WITH_ENV=true
      ;;
    --dry-run)
      DRY_RUN=true
      ;;
    -h|--help)
      echo "Usage: $0 [--with-env] [--dry-run]"
      echo ""
      echo "Environment overrides:"
      echo "  SYNC_SERVER, SYNC_USER, SYNC_PORT, SYNC_REMOTE_DIR"
      exit 0
      ;;
  esac
done

cd "$PROJECT_ROOT"

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
  echo "[sync] Dry run mode"
fi

DEST="${SYNC_USER}@${SYNC_SERVER}:${SYNC_REMOTE_DIR}"
echo "[sync] Source: $PROJECT_ROOT"
echo "[sync] Target: $DEST"

rsync "${RSYNC_OPTS[@]}" \
  --rsh="ssh -p ${SYNC_PORT} -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new" \
  ./ \
  "${DEST}/"

echo "[sync] Done"
if [ "$DRY_RUN" = false ] && [ "$WITH_ENV" = false ]; then
  echo "[sync] .env.production not synced by default"
fi

echo "[sync] WARNING: Do not use this script for production release."

