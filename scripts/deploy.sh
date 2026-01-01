#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export DJANGO_SETTINGS_MODULE=config.settings.base

printf "[%s] running deploy script\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

python manage.py migrate
python hrms/apply_triggers.py
python hrms/apply_views.py
python manage.py collectstatic --noinput
python manage.py check
