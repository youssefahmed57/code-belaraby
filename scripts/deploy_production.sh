#!/bin/bash
set -e

echo "=== Starting Production Deployment for Code Journey Academy ==="

if [ ! -f .env.production ]; then
  echo "Error: .env.production file not found!"
  exit 1
fi

echo "[1/5] Creating Database Pre-deployment Backup..."
./scripts/backup_db.sh production

echo "[2/5] Pulling latest git release..."
git pull origin main

echo "[3/5] Building and starting Production containers..."
docker compose -f docker-compose.yml -f docker-compose.production.yml --env-file .env.production up -d --build --remove-orphans

echo "[4/5] Running DB Migrations..."
docker compose -f docker-compose.yml -f docker-compose.production.yml exec -T backend python -m alembic upgrade head

echo "[5/5] Verifying health and readiness..."
sleep 5
curl -f http://127.0.0.1:8000/health || (echo "Health check failed!" && exit 1)
curl -f http://127.0.0.1:8000/ready || (echo "Readiness probe failed!" && exit 1)

echo "=== Production Deployment Complete! ==="
