#!/bin/bash
set -e

echo "=== Starting Staging Deployment for Code Journey Academy ==="

if [ ! -f .env.staging ]; then
  echo "Error: .env.staging file not found!"
  exit 1
fi

echo "[1/4] Pulling latest git commit..."
git pull origin staging

echo "[2/4] Building and starting Staging containers..."
docker compose -f docker-compose.yml -f docker-compose.staging.yml --env-file .env.staging up -d --build --remove-orphans

echo "[3/4] Running DB Migrations..."
docker compose -f docker-compose.yml -f docker-compose.staging.yml exec -T backend python -m alembic upgrade head

echo "[4/4] Verifying health and readiness..."
sleep 5
curl -f http://127.0.0.1:8000/health || (echo "Health check failed!" && exit 1)
curl -f http://127.0.0.1:8000/ready || (echo "Readiness probe failed!" && exit 1)

echo "=== Staging Deployment Complete! ==="
