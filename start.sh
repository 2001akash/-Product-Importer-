#!/bin/bash
set -e

echo "=========================================="
echo "Starting ACME Product Importer"
echo "=========================================="

echo "Starting Celery worker in background..."
nohup celery -A tasks.celery_app.celery worker --loglevel=info --concurrency=2 > /tmp/celery.log 2>&1 &

sleep 2

echo "Starting FastAPI application on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
