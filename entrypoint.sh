#!/bin/bash

# Exit on error
set -e

# Run migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files (optional)
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn medical_coding_project.wsgi:application --bind 0.0.0.0:8000
