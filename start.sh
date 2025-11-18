#!/bin/bash
set -e

echo "=========================================="
echo "Starting ACME Product Importer"
echo "=========================================="

echo "Starting Celery worker in background..."
celery -A tasks.celery_app.celery worker --loglevel=info --concurrency=2 &

# Give Celery a moment to initialize
sleep 3

echo "Starting FastAPI application on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}