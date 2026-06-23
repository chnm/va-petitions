# CLAUDE.md

This file provides guidance to Claude when working with code in this repository.

## Project Overview

"By Petition" — a Django web portal for ~3,700 digitized petitions from the Library of Virginia (1773–1861), including legislative petitions and Revolutionary War pension declarations. Petitions are linked to modern counties across VA, WV, KY, and PA via many-to-many relationships. The site title is "Laid Before the Assembly."

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

- **`config/`** — Django project settings, root URL conf (`config/urls.py` includes both `petitions.urls` and `pages.urls` at root).
- **`petitions/`** — Core app. Models: `Petition` (with `kind`, `primary_theme` fields), `County` (with state: VA/WV/KY/PA), `Subject`. Petitions connect to counties and subjects via M2M. Views: catalog (server-side paginated), map (Leaflet + AJAX detail panel), search (server-side), petition detail, county list/detail.
- **`pages/`** — Home, about, and two model-backed content pages: Introduction essay (`Essay`) and Educational Resources (`ResourcePage` + `Resource` cards). `Essay`/`ResourcePage` are admin-edited singletons (`has_add_permission` guard); their Markdown body fields render via the `markdown` lib.
- **`theme/`** — django-tailwind app (v4 standalone, no Node required). Source CSS in `theme/static_src/src/styles.css`. Built CSS output in `theme/static/css/dist/styles.css`.
- **`templates/`** — Project-level templates. `base.html` includes masthead, footer, and loads Tailwind + Google Fonts.
- **`static/img/`** — Footer logos (chnm-logo.png, gmu-logo.png).

## URL Structure

- `/` — Home ("Laid Before the Assembly")
- `/introduction/` — Interpretive essay (singleton `Essay`, Markdown body with footnotes → Notes, pull quotes)
- `/catalog/` — Paginated catalog with type/subject/locality filters
- `/map/` — Leaflet map with county markers, ranked panel, subject + year-range filter bar, AHCB boundary toggle
- `/map/county/<slug>/` — AJAX endpoint returning petitions for a county (JSON); honors `?subject=&from=&to=` filters
- `/search/?q=` — Server-side search across title, description, locality, subjects
- `/resources/` — Educational Resources cards (`Resource`), linking out to teachinghistory.org
- `/health/` — Liveness check returning `{"status":"ok","code":200}` for the Docker host to poll
- `/#about` — About section on home page
- `/admin/` — Django admin

## Data Model

- **Petition**: `serial` (unique), `title`, `petition_type` (legislative/pension), `kind` (Petition/Remonstrance/Counter-Petition), `primary_theme` (6 choices, optional), `date`, `description`, `locality_raw`, `permalink`, `rosetta_ie`. M2M to County and Subject.
- **County**: `name`, `slug` (prefixed with state code, e.g., `va-accomack-county`), `state`, `latitude`, `longitude`. The M2M relationship to Petition is the geographic truth — not `locality_raw`.
- **Subject**: `name`, `slug`. 39 topical categories from the CSV import.

## Data Import

The CSV import (`import_petitions`) maps the spreadsheet's binary Yes/No county columns directly to M2M relationships — this is the source of truth for geographic assignments, not the `Locality` text field. County slugs are prefixed with state code. Subjects come from both binary columns and the semicolon-delimited `Subject` field.

Two import paths share the transform logic in `petitions/lva.py`: the `import_petitions` command (bulk/initial CLI loads) and a django-import-export `PetitionResource` (admin **Import** button on the Petition changelist; `.xlsx`/`.csv`, keyed on `Serial` — edit existing or append new, with a dry-run preview). The admin import *replaces* a petition's counties/subjects from the sheet. VA/WV county names are unique (the two states never share a name), so binary columns resolve by name; KY/PA counties come from the semicolon locality columns. New counties/subjects not already in the DB aren't auto-created from binary columns.

## Map

The map view (`/map/`) uses Leaflet with CARTO tiles. A filter bar above the map holds a subject dropdown and a dual-handle year range; the view sends a compact per-petition dataset (year + county/subject indices) and the browser recomputes county counts, markers, and the ranked panel live as filters change (full year span = "All years", includes undated petitions). Markers are sized by `sqrt(count)` with opacity scaled relative to the *filtered* max (kept in sync with the panel bars — relative, not global, since War Claims/Pensions dominates). Clicking a county fetches its petitions via AJAX and pans/zooms; hovering a panel row highlights its bubble (the selected county keeps its ring). Historical county boundaries come from the AHCB API (`data.chnm.org/ahcb/counties/{date}/state-code/va,wv,ky,pa/`) and snap to the year range's end (the API takes a single date, not a range); boundary polygons use `interactive: false` so clicks fall through to markers. The API uses modern state codes even for historical dates.

## Design System

### Fonts (Google Fonts)
- **Libre Caslon Display** (`font-display`) — large display headings
- **Libre Caslon Text** (`font-serif`) — body copy, record titles
- **Courier Prime** (`font-mono`) — nav, labels, metadata, dates, counts, buttons

### Color Tokens (defined in `theme/static_src/src/styles.css`)
- `paper` #f3ede1 (background), `paper-alt` #efe7d7, `paper-deep` #ece4d4 (hover)
- `ink` #221d16 (primary text), `ink-soft` #574d3f, `ink-soft-2` #3f382d
- `meta` #8a7f6c (metadata), `accent` #7c3a2d (links, active states)
- `rule` #d9cfb9 (dividers), `border` #cabfa6 (inputs, panels), `field` #fbf8f0 (input fills)
- Footer colors: `footer-text`, `footer-label`, `footer-rule`, `footer-strong`

### Layout
- Content max-width: 1280px (search page: 880px)
- Side padding: 56px (`px-14`)
- Use Tailwind utility classes in templates; component CSS for Markdown-rendered HTML and custom widgets (`.essay-body`, `.dual-range`) lives in `theme/static_src/src/styles.css`
- Rebuild Tailwind after template changes: `uv run python manage.py tailwind build`

## Style Conventions

- Do not commit the source CSV or `statement.md` (kept untracked)
- Group git commits logically by concern
- `::selection` styled with oxblood accent (#7c3a2d on #f3ede1)
- Beta banner is present at top of all pages (in base.html)
