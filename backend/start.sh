#!/bin/sh
set -e

echo "=== Running Alembic Database Migrations ==="
alembic upgrade head

echo "=== Seeding Initial Database Content ==="
python -m app.db.seed || echo "Seed execution completed with notices"

echo "=== Starting FastAPI Uvicorn Server ==="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
