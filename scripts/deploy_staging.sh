#!/bin/bash
set -e

echo "=== Starting Staging Deployment for Code Belaraby ==="

if [ ! -f .env.staging ]; then
  echo "Error: .env.staging file not found!"
  exit 1
fi

# Load RUN_SEED from .env.staging if present, default to false
RUN_SEED=${RUN_SEED:-false}

echo "[1/4] Pulling latest git commit..."
git pull origin staging

echo "[2/4] Building and starting Staging containers..."
docker compose -f docker-compose.yml -f docker-compose.staging.yml --env-file .env.staging up -d --build --remove-orphans

echo "[3/4] Running DB Migrations..."
docker compose -f docker-compose.yml -f docker-compose.staging.yml exec -T backend python -m alembic upgrade head

if [ "$RUN_SEED" = "true" ]; then
  echo "[3.1/4] Seeding initial database data (RUN_SEED=true)..."
  docker compose -f docker-compose.yml -f docker-compose.staging.yml exec -T backend python app/db/seed.py
else
  echo "[3.1/4] Skipping database seed (RUN_SEED=false)."
fi

echo "[4/4] Verifying health and readiness..."
sleep 5
curl -f http://127.0.0.1:8000/health || (echo "Health check failed!" && exit 1)
curl -f http://127.0.0.1:8000/ready || (echo "Readiness probe failed!" && exit 1)

echo "=== Staging Deployment Complete! ==="
