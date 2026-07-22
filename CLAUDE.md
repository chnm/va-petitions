# CLAUDE.md

This file provides guidance to Claude when working with code in this repository.

1. No destructive commands without warning — before suggesting anything that stops, removes, recreates, or changes ports on something currently running, warn explicitly and ask for confirmation first.
2. One plan, with a checkpoint — decide the right approach before answering, give one linear plan, never pivot mid-answer. For anything above a certain threshold (destructive actions, new architecture/infra decisions, spending money, genuinely ambiguous asks), present the plan with tradeoffs and wait for a go-ahead. Otherwise just proceed.
3. Code blocks are copy-paste only — no conversational text or explanations inside code blocks, ever. Just functional, ready-to-run content.
4. Default to action — if a task is clear and below that checkpoint threshold, execute it end-to-end without asking permission. No delivering a stub and calling it finished — partial work gets flagged as partial.
5. Structured capture of decisions — when a conversation builds up real working knowledge or decisions worth keeping, offer once to save a summary (never do it automatically).
6. Calibrated initiative — passive answering is a failure mode. If there's a real risk, better approach, or sharper question I should've asked, add it briefly after the main answer — not as a mid-answer detour. Disagree directly when something's wrong instead of hedging.
7. Finish the whole ask — when given a list, do all of it. No silently deprioritizing or dropping items. "Done" means actually shipped/deployed and visible, not just written or committed somewhere.

## Project Overview

"Records of Revolution" — a Django portal for ~3,700 digitized legal records from the Library of Virginia (1773–1861), including legislative petitions, Revolutionary War pension declarations, and related records. Records are linked to modern counties across VA, WV, KY, and PA via many-to-many relationships. The homepage subtitle is "War, Rights, Family, and Freedom in Virginia’s Legal Records."

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

- `/` — Home ("Records of Revolution")
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
- `paper` #f3ede1 (background), `card` #f6f0e4, `paper-alt` #efe7d7, `paper-deep-2` #e4dcc8 (thumbnails)
- `ink` #221d16 (primary text), `ink-soft` #574d3f, `ink-soft-2` #3f382d
- `meta` #6f6555 (accessible metadata on paper), `accent` / `blue` #26415c (links, active states, structural fields)
- `blue-deep` #1b2b3a (footer), `blue-text` #c3ccd4, `blue-text-muted` #9fb0c1
- `rust` #7c3a2d (petition voice and true emphasis)
- `ochre` #c9a86a and `ochre-light` #e4c58a (labels and dividers on blue)
- `rule` #d9cfb9 (decorative dividers), `border` #8a7f6c (input and panel boundaries), `field` #fbf8f0 (input fills)
- Footer colors: `footer-text`, `footer-label`, `footer-rule`

### Layout
- Primary content max-width: 1440px, with narrower prose measures inside that frame
- Side padding: 24px mobile, 40px tablet, 56px desktop
- Page headers use the full-bleed blue field; standard headers share `templates/partials/page_hero.html`
- Use Tailwind utility classes in templates; component CSS for Markdown-rendered HTML and custom widgets (`.essay-body`, `.dual-range`) lives in `theme/static_src/src/styles.css`
- Rebuild Tailwind after template changes: `uv run python manage.py tailwind build`

## Style Conventions

- Admin uses **django-unfold**; new `ModelAdmin` classes must inherit `unfold.admin.ModelAdmin` (not the plain Django base). `unfold` + `unfold.contrib.import_export` precede `django.contrib.admin` in `INSTALLED_APPS`; `PetitionAdmin` uses Unfold's import/export forms.
- Do not commit the source CSV or `statement.md` (kept untracked)
- Group git commits logically by concern
- `::selection` styled with oxblood accent (#7c3a2d on #f3ede1)
- Beta banner is present at top of all pages (in base.html)
