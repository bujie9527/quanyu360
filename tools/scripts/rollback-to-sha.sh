#!/usr/bin/env sh

set -eu

if [ "$#" -lt 1 ]; then
  echo "Usage: sh tools/scripts/rollback-to-sha.sh <commit_sha> [branch]" >&2
  exit 1
fi

TARGET_SHA="$1"
BRANCH="${2:-main}"
ENV_FILE_PATH="${ENV_FILE_PATH:-.env.production}"
SMOKE_CHECK_MODE="${SMOKE_CHECK_MODE:-proxy}"
SMOKE_CHECK_BASE_URL="${SMOKE_CHECK_BASE_URL:-http://127.0.0.1}"
DEPLOY_HISTORY_DIR="${DEPLOY_HISTORY_DIR:-.deploy-history}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Current directory is not a git repository: $(pwd)" >&2
  exit 1
fi

git fetch --prune origin

git checkout "$BRANCH"

if ! git rev-parse --verify "$TARGET_SHA^{commit}" >/dev/null 2>&1; then
  echo "Commit not found: $TARGET_SHA" >&2
  exit 1
fi

echo "[rollback] Resetting $BRANCH to $TARGET_SHA"
git reset --hard "$TARGET_SHA"

ROLLED_SHA="$(git rev-parse --short HEAD)"
ROLLBACK_TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

ENV_FILE_PATH="$ENV_FILE_PATH" sh tools/scripts/deploy.sh
SMOKE_CHECK_MODE="$SMOKE_CHECK_MODE" SMOKE_CHECK_BASE_URL="$SMOKE_CHECK_BASE_URL" sh tools/scripts/smoke-check.sh

mkdir -p "$DEPLOY_HISTORY_DIR"
echo "$ROLLBACK_TS rollback $ROLLED_SHA" >> "$DEPLOY_HISTORY_DIR/rollback.log"

echo "[rollback] Completed at $ROLLBACK_TS, running commit: $ROLLED_SHA"