#!/bin/sh
set -eu

# Use poetry run instead of activating virtual environment

# Collect static files if required
if [ "${COLLECT_STATIC:-0}" = "1" ]; then
    echo "Collecting static files..."
    poetry run python manage.py collectstatic --noinput
fi

# Apply database migrations
echo "Applying database migrations..."
poetry run python manage.py migrate

# Start the main process
echo "Starting Gunicorn server..."
exec poetry run python -m gunicorn config.wsgi:application --bind "${GUNICORN_BIND:-0.0.0.0:8000}"
