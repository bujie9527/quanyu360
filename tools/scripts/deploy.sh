#!/usr/bin/env sh

set -eu

ENV_FILE_PATH="${ENV_FILE_PATH:-.env.production}"
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"

if [ ! -f "$ENV_FILE_PATH" ]; then
  echo "Environment file not found: $ENV_FILE_PATH" >&2
  echo "Create it from .env.production.example first." >&2
  exit 1
fi

echo "Validating Docker Compose configuration with $ENV_FILE_PATH..."
ENV_FILE="$ENV_FILE_PATH" docker compose --env-file "$ENV_FILE_PATH" $COMPOSE_FILES config >/dev/null

echo "Building and starting production stack..."
ENV_FILE="$ENV_FILE_PATH" docker compose --env-file "$ENV_FILE_PATH" $COMPOSE_FILES up --build -d

echo "Running database migrations (alembic upgrade head)..."
ENV_FILE="$ENV_FILE_PATH" docker compose --env-file "$ENV_FILE_PATH" $COMPOSE_FILES exec -T project-service sh -lc "cd /app/backend && alembic upgrade head"

echo "Seeding WordPress install workflow (idempotent)..."
ENV_FILE="$ENV_FILE_PATH" docker compose --env-file "$ENV_FILE_PATH" $COMPOSE_FILES exec -T project-service sh -lc "cd /app/backend && python scripts/seed_wp_site_install_workflow.py || true"

echo "Deployment started successfully."
echo "Public entrypoint should be available on NGINX port defined by NGINX_HTTP_PORT."
