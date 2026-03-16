#!/usr/bin/env sh

set -eu

echo "Running platform smoke checks..."

MODE="${SMOKE_CHECK_MODE:-direct}"
BASE_URL="${SMOKE_CHECK_BASE_URL:-http://localhost}"

if [ "$MODE" = "proxy" ]; then
  endpoints="
$BASE_URL/health/live
$BASE_URL/
$BASE_URL/api/auth/health/live
$BASE_URL/api/projects
$BASE_URL/api/agents
$BASE_URL/api/tasks/analytics
$BASE_URL/api/workflows
$BASE_URL/api/executions
$BASE_URL/api/runtime/analytics/summary
"
else
  endpoints="
http://localhost:8001/health/live
http://localhost:8002/health/live
http://localhost:8003/health/live
http://localhost:8004/health/live
http://localhost:8005/health/live
http://localhost:8100/health/live
http://localhost:8200/health/live
http://localhost:3000
"
fi

printf "%s\n" "$endpoints" | while IFS= read -r endpoint; do
  [ -n "$endpoint" ] || continue
  printf "Checking %s\n" "$endpoint"
  curl --fail --silent --show-error "$endpoint" >/dev/null
done

echo "All endpoints responded successfully."
