#!/bin/sh
set -e

echo "Running migrations..."

alembic upgrade head

echo "Starting app..."

exec gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8051 \
    --worker-connections 1000 main:app
