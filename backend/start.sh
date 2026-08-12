#!/bin/sh
set -eu

echo "=== Waiting for Database Connection ==="
sleep 3

echo "=== Running Alembic Database Migrations ==="
alembic upgrade head

if [ "${RUN_SEED:-false}" = "true" ]; then
  echo "=== Seeding Initial Database Content ==="
  python -m app.db.seed
fi

echo "=== Starting FastAPI Uvicorn Server ==="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
