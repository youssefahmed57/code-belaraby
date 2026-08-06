#!/usr/bin/env bash
set -e

echo "=== Starting Render Web Service for Code Belaraby ==="

echo "[1/2] Running Alembic Database Migrations..."
python -m alembic upgrade head

if [ "$RUN_SEED" = "true" ]; then
  echo "[1.1/2] Seeding database (RUN_SEED=true)..."
  python app/db/seed.py
else
  echo "[1.1/2] Skipping database seed (RUN_SEED=false)."
fi

echo "[2/2] Starting Uvicorn Web Server on Port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
