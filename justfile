# Show available commands
default:
    @just --list

# Development Commands
# ====================

# Start the Django development server
preview:
    uv run python manage.py runserver

# Watch and rebuild Tailwind CSS (run alongside `just preview`)
tailwind:
    uv run python manage.py tailwind start

# One-time Tailwind CSS build
tailwind-build:
    uv run python manage.py tailwind build

# Check for any issues with the Django configuration
check:
    uv run python manage.py check

# Open Django shell for interactive debugging
shell:
    uv run python manage.py shell

# Database Management
# ===================

# Create new migration files based on model changes
mm:
    uv run python manage.py makemigrations

# Apply migrations to the database
migrate:
    uv run python manage.py migrate

# Show migration status
show-migrations:
    uv run python manage.py showmigrations

# Utility Commands
# ================

# Create a superuser account
superuser:
    uv run python manage.py createsuperuser

# Collect static files (for production)
collectstatic: tailwind-build
    uv run python manage.py collectstatic --noinput

# Run tests
test *args:
    uv run python manage.py test {{ args }}

# Check code with ruff
ruff-check:
    uvx ruff check

# Format code with ruff
fmt:
    uvx ruff format .

# Format HTML templates with djhtml
fmt-html:
    uv run djhtml templates/
