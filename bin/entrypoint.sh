#!/bin/sh

set -e

if [ "${MIGRATE:-false}" = "true" ]; then
    echo "Applying database migrations..."
    uv run alembic upgrade head
    echo "Migrations applied."
fi


GUNICORN_HOST=${APP_HOST:-0.0.0.0}
GUNICORN_PORT=${APP_PORT:-8004}
GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT:-600}
GUNICORN_WORKERS=${GUNICORN_WORKERS:-4}

echo "Starting FastAPI app ..."
exec gunicorn src.main.web:create_app \
    -k app.core.gunicorn_conf.CustomUvicornWorker \
    -w $GUNICORN_WORKERS \
    -b $GUNICORN_HOST:$GUNICORN_PORT \
    --timeout $GUNICORN_TIMEOUT \
    --access-logfile - \
    --error-logfile -
