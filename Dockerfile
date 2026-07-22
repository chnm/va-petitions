# syntax=docker/dockerfile:1
# ---------------------------------------------------------------------------
# "Records of Revolution" — Django portal image.
#
# Single glibc stage. No Node: django-tailwind 4.x is standalone
# (pytailwindcss), so the old Volta-built-from-Rust bootstrap is gone.
#
# Built to run under the standard CHNM compose stack, whose app service does:
#   command: sh -c "uv run manage.py migrate && uv run manage.py runserver 0.0.0.0:8000"
# Compose `command` overrides CMD but NOT ENTRYPOINT, so this image has NO
# ENTRYPOINT and keeps `uv` on PATH. Config is env-driven (config/settings.py);
# the SQLite database lives on a mounted volume (SQLITE_PATH).
# ---------------------------------------------------------------------------
FROM python:3.13-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/venv/bin:$PATH \
    DJANGO_SETTINGS_MODULE=config.settings \
    SQLITE_PATH=/data/db.sqlite3
WORKDIR /app

# Dependencies first, so editing a template doesn't reinstall Django.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# App source, then build the stylesheet and collect static for WhiteNoise.
# pytailwindcss fetches the standalone tailwindcss v4 binary; @source globs in
# styles.css scan /app for class names. collectstatic populates STATIC_ROOT so
# WhiteNoise serves assets when DEBUG is off. Env defaults in settings.py let
# both commands run at build time without a database.
COPY . .
RUN uv run python manage.py tailwind build \
    && test -s theme/static/css/dist/styles.css \
    && uv run python manage.py collectstatic --no-input

# The SQLite DB defaults to /data/db.sqlite3 (SQLITE_PATH above); create the dir
# so mounting a volume at /data is all a deploy needs to persist data — no env
# var to remember. (Host-run Django still defaults to ./db.sqlite3.)
RUN mkdir -p /data

EXPOSE 8000

# No Docker HEALTHCHECK: this site doesn't use the autoheal sidecar. The app
# still exposes /health/ (liveness JSON) for manual or external polling.

# No ENTRYPOINT: the compose `command` (sh -c "... uv run ...") runs verbatim.
# This default CMD just makes a bare `docker run` self-sufficient.
CMD ["sh", "-c", "uv run manage.py migrate && uv run manage.py runserver 0.0.0.0:8000"]
