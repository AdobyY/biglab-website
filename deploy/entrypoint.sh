#!/bin/sh
set -eu

# Volumes are mounted after the image is built. Prepare their ownership before
# dropping privileges; Django and Gunicorn always run as the application user.
SQLITE_PATH="${SQLITE_PATH:-/data/db.sqlite3}"
MEDIA_ROOT="${MEDIA_ROOT:-/data/media}"
export SQLITE_PATH MEDIA_ROOT

if [ "$(id -u)" = "0" ]; then
    mkdir -p /data/media
    chown -R wagtail:wagtail /data
    exec gosu wagtail /bin/sh "$0" "$@"
fi

# Preserve one-off maintenance commands used by Docker Compose.
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

python manage.py migrate --noinput
if [ "${SEED_INITIAL_CONTENT:-0}" = "1" ]; then
    python manage.py seed_biglab --if-changed
fi
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 1 --threads 2 --timeout 60
