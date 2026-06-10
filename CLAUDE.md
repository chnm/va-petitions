# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Django web portal for ~3,700 digitized petitions from the Library of Virginia (1773–1861), including legislative petitions and Revolutionary War pension declarations. Petitions are linked to modern counties across VA, WV, KY, and PA via many-to-many relationships.

## Commands

```bash
uv run python manage.py runserver          # Start dev server
uv run python manage.py tailwind start     # Watch/rebuild Tailwind CSS (run alongside runserver)
uv run python manage.py tailwind build     # One-time Tailwind CSS build
uv run python manage.py migrate            # Apply migrations
uv run python manage.py makemigrations     # Generate migrations after model changes
uv run python manage.py import_petitions <csv_file> [--clear]  # Import from LVA CSV
uv run python manage.py geocode_counties [--overwrite]         # Populate county lat/lng via Nominatim
```

## Architecture

- **`config/`** — Django project settings, root URL conf. Templates dir is `templates/` at project root.
- **`petitions/`** — Core app. Models: `Petition`, `County` (with state: VA/WV/KY/PA), `Subject`. Petitions connect to counties and subjects via M2M. Views handle list/detail for petitions and counties, plus a Leaflet map view.
- **`pages/`** — Static content pages (home, about, teaching). Imports from `petitions.models` for homepage stats.
- **`theme/`** — django-tailwind app (v4 standalone, no Node required). Source CSS in `theme/static_src/src/styles.css`. Built CSS output in `theme/static/css/dist/styles.css`.
- **`templates/`** — Project-level templates. `base.html` loads Tailwind and Google Fonts (Inter + JetBrains Mono).

## Data Import

The CSV import (`import_petitions`) maps the spreadsheet's binary Yes/No county columns directly to M2M relationships — this is the source of truth for geographic assignments, not the `Locality` text field. County slugs are prefixed with state code (e.g., `va-accomack-county`). Subjects come from both binary columns and the semicolon-delimited `Subject` field.

## Map

The map view (`/petitions/map/`) uses Leaflet with CARTO tiles. Historical county boundaries are fetched client-side from the AHCB API (`data.chnm.org/ahcb/counties/{date}/state-code/va,wv,ky,pa/`). The API uses modern state codes even for historical dates (e.g., `wv` returns pre-1863 Virginia counties in the WV area).

## Style Conventions

- **Inter** as body font (`font-sans`), **JetBrains Mono** for dates, counts, serial numbers (`font-mono`)
- Link color: `text-red-800`
- Use Tailwind utility classes in templates; no separate CSS files
