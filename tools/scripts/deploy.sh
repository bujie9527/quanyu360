#!/usr/bin/env sh

set -eu

ENV_FILE_PATH="${ENV_FILE_PATH:-.env.production}"
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"

compose() {
  ENV_FILE="$ENV_FILE_PATH" docker compose --env-file "$ENV_FILE_PATH" $COMPOSE_FILES "$@"
}

if [ ! -f "$ENV_FILE_PATH" ]; then
  echo "Environment file not found: $ENV_FILE_PATH" >&2
  echo "Create it from .env.production.example first." >&2
  exit 1
fi

if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  DEPLOY_SHA="$(git rev-parse --short HEAD || true)"
  if [ -n "$DEPLOY_SHA" ]; then
    echo "Deploying git revision: $DEPLOY_SHA"
  fi
fi

echo "Validating Docker Compose configuration with $ENV_FILE_PATH..."
compose config >/dev/null

echo "Collecting migration baseline..."
compose exec -T project-service sh -lc "cd /app/backend && alembic current || true"

SCHEMA_FINGERPRINT="$(compose exec -T postgres sh -lc '
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atqc "
  SELECT
    CASE WHEN to_regclass('"'"'public.alembic_version'"'"') IS NULL
      THEN '"'"''"'"'
      ELSE COALESCE((SELECT version_num FROM alembic_version LIMIT 1), '"'"''"'"')
    END,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name='"'"'projects'"'"' AND column_name IN ('"'"'project_type'"'"','"'"'matrix_config'"'"')),
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='"'"'public'"'"' AND table_name IN ('"'"'site_plans'"'"','"'"'site_plan_items'"'"')),
    (SELECT COUNT(*) FROM pg_type WHERE typname IN ('"'"'project_type'"'"','"'"'site_plan_status'"'"','"'"'site_plan_item_status'"'"')),
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='"'"'public'"'"' AND table_name IN ('"'"'servers'"'"')),
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name='"'"'platform_domains'"'"' AND column_name='"'"'server_id'"'"'),
    (SELECT COUNT(*) FROM pg_type WHERE typname='"'"'server_status'"'"');
  "
')"

IFS='|' read -r CURRENT_DB_REV PROJECT_COLS SITE_PLAN_TABLES ENUMS_0025 SERVERS_TABLE DOMAIN_SERVER_COL SERVER_ENUM <<EOF
$SCHEMA_FINGERPRINT
EOF

ARTIFACT_0025=$((PROJECT_COLS + SITE_PLAN_TABLES + ENUMS_0025))
ARTIFACT_0026=$((SERVERS_TABLE + DOMAIN_SERVER_COL + SERVER_ENUM))

if [ -z "$CURRENT_DB_REV" ] && [ $((ARTIFACT_0025 + ARTIFACT_0026)) -gt 0 ]; then
  echo "Migration drift detected: schema already has post-0024 artifacts but alembic_version is empty." >&2
  echo "Resolve drift first (stamp + verify), then rerun deploy." >&2
  exit 1
fi

if [ "$CURRENT_DB_REV" = "20260310_0024" ] && [ $((ARTIFACT_0025 + ARTIFACT_0026)) -gt 0 ]; then
  echo "Migration drift detected: DB revision is 20260310_0024 but newer schema artifacts already exist." >&2
  echo "Resolve drift first (stamp + verify), then rerun deploy." >&2
  exit 1
fi

if [ "$CURRENT_DB_REV" = "20260316_0025" ] && [ "$ARTIFACT_0026" -gt 0 ]; then
  echo "Migration drift detected: DB revision is 20260316_0025 but 0026 artifacts already exist." >&2
  echo "Resolve drift first (stamp + verify), then rerun deploy." >&2
  exit 1
fi

echo "Building and starting production stack..."
compose up --build -d

echo "Running database migrations (alembic upgrade head)..."
if ! compose exec -T project-service sh -lc "cd /app/backend && alembic upgrade head"; then
  echo "Migration failed. Check alembic status and runbook before retry." >&2
  exit 1
fi

echo "Seeding WordPress install workflow (idempotent)..."
compose exec -T project-service sh -lc "cd /app/backend && python scripts/seed_wp_site_install_workflow.py || true"

echo "Deployment started successfully."
echo "Public entrypoint should be available on NGINX port defined by NGINX_HTTP_PORT."