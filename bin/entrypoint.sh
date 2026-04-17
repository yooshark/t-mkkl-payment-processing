#!/bin/sh

set -e

echo "=============================="
echo "[ENTRYPOINT] START"
echo "=============================="

echo "[DEBUG] Current user: $(whoami)"
echo "[DEBUG] Current dir: $(pwd)"
echo "[DEBUG] MIGRATE=$MIGRATE"
echo "[DEBUG] PATH:"
echo "$PATH"

if [ "${MIGRATE:-false}" = "true" ]; then
    echo "Applying database migrations..."

    echo "[DEBUG] Alembic check:"
    uv run alembic --version || true

    echo "[DEBUG] Alembic config check:"
    ls -la alembic.ini || true
    ls -la /code/alembic.ini || true
    echo "[DEBUG] Running alembic upgrade..."

    alembic -c alembic.ini upgrade head
    echo "Migrations applied."
fi


GUNICORN_HOST=${APP_HOST:-0.0.0.0}
GUNICORN_PORT=${APP_PORT:-8004}
GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT:-600}
GUNICORN_WORKERS=${GUNICORN_WORKERS:-4}

echo "Starting FastAPI app ..."
exec gunicorn src.main.web:create_app \
    -k src.main.gunicorn_conf.CustomUvicornWorker \
    -w $GUNICORN_WORKERS \
    -b $GUNICORN_HOST:$GUNICORN_PORT \
    --timeout $GUNICORN_TIMEOUT \
    --access-logfile - \
    --error-logfile -

exec "$@"
