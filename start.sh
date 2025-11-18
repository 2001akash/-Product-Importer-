#!/bin/bash
set -e

echo "====================="
echo "Starting Celery worker"
echo "====================="
nohup celery -A tasks.celery_app.celery worker --loglevel=info --concurrency=2 > /tmp/celery.log 2>&1 &

sleep 2

echo "====================="
echo "Starting FastAPI"
echo "====================="
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
