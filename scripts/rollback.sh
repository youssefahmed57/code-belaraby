#!/bin/bash
set -e

ENV=${1:-staging}
PREV_COMMIT=${2:-HEAD~1}

echo "=== Initiating Rollback for environment: $ENV to commit: $PREV_COMMIT ==="

if [ "$ENV" = "staging" ]; then
  ENV_FILE=".env.staging"
  COMPOSE_FILE="docker-compose.staging.yml"
else
  ENV_FILE=".env.production"
  COMPOSE_FILE="docker-compose.production.yml"
fi

echo "[1/3] Reverting git repository to $PREV_COMMIT..."
git checkout $PREV_COMMIT

echo "[2/3] Re-building and restarting containers..."
docker compose -f docker-compose.yml -f $COMPOSE_FILE --env-file $ENV_FILE up -d --build --remove-orphans

echo "[3/3] Checking container health status..."
sleep 5
curl -f http://127.0.0.1:8000/health || (echo "Rollback health check failed!" && exit 1)

echo "=== Rollback Successful! ==="
