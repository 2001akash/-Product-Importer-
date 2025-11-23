#!/bin/bash

# 1. Start Celery in the background
# We use '&' to put it in the background so the script continues to the next line.
echo "Starting Celery worker..."
celery -A tasks.celery_app.celery worker --loglevel=info &

# 2. Wait a moment for Celery to initialize (optional but helpful)
sleep 5

# 3. Start FastAPI
# We use 'exec' so that uvicorn becomes the main process (PID 1).
# This allows it to receive shutdown signals correctly.
echo "Starting FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}