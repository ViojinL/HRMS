#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export DJANGO_SETTINGS_MODULE=config.settings.base

printf "[%s] entrypoint: running migrations and collectstatic\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
python manage.py migrate
python hrms/apply_triggers.py
python hrms/apply_views.py
python manage.py collectstatic --noinput

printf "[%s] entrypoint: starting Gunicorn\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --log-level info
