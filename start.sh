#!/bin/bash
set -e

echo "Starting application..."

# Only run migrations if database URL is available
if [ ! -z "$DATABASE_URL" ]; then
    echo "Running database migrations..."
    python -m alembic upgrade head
else
    echo "DATABASE_URL not available, skipping migrations"
fi

echo "Starting FastAPI server..."
exec python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT