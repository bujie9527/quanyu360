#!/usr/bin/env sh

set -eu

BRANCH="${BRANCH:-main}"
ENV_FILE_PATH="${ENV_FILE_PATH:-.env.production}"
SMOKE_CHECK_MODE="${SMOKE_CHECK_MODE:-proxy}"
SMOKE_CHECK_BASE_URL="${SMOKE_CHECK_BASE_URL:-http://127.0.0.1}"
DEPLOY_HISTORY_DIR="${DEPLOY_HISTORY_DIR:-.deploy-history}"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required on the deployment server." >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Current directory is not a git repository: $(pwd)" >&2
  exit 1
fi

mkdir -p "$DEPLOY_HISTORY_DIR"

echo "[deploy-from-git] Fetching remote branch: $BRANCH"
git fetch --prune origin

echo "[deploy-from-git] Checking out branch: $BRANCH"
git checkout "$BRANCH"

echo "[deploy-from-git] Resetting to origin/$BRANCH"
git reset --hard "origin/$BRANCH"

DEPLOY_SHA="$(git rev-parse --short HEAD)"
DEPLOY_TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

echo "[deploy-from-git] Deploying commit: $DEPLOY_SHA"
ENV_FILE_PATH="$ENV_FILE_PATH" sh tools/scripts/deploy.sh

echo "[deploy-from-git] Running smoke checks..."
SMOKE_CHECK_MODE="$SMOKE_CHECK_MODE" SMOKE_CHECK_BASE_URL="$SMOKE_CHECK_BASE_URL" sh tools/scripts/smoke-check.sh

echo "$DEPLOY_TS $DEPLOY_SHA" >> "$DEPLOY_HISTORY_DIR/success.log"
tail -n 3 "$DEPLOY_HISTORY_DIR/success.log" > "$DEPLOY_HISTORY_DIR/recent-successful-shas.log"

echo "[deploy-from-git] Done. Commit: $DEPLOY_SHA"