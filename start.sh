#!/bin/bash

echo "Starting Celery worker..."
nohup celery -A tasks.celery_app.celery worker --loglevel=info > /tmp/celery.log 2>&1 &

sleep 2

echo "Starting FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
