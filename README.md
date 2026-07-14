# Virginia Petitions

A Django web portal for exploring ~3,700 digitized petitions from the Library of Virginia, spanning 1773–1861. The collection includes legislative petitions to the General Assembly and Revolutionary War pension declarations.

## Features

- Browse petitions by type, subject, county, or date
- Interactive map with petition counts per county (VA, WV, KY, PA)
- Toggleable historical county boundaries via the [Atlas of Historical County Boundaries](https://digital.newberry.org/ahcb/) API
- Links to digitized petition images in the LVA's Rosetta digital repository
- Django admin for data management

## Setup

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py import_petitions <path-to-csv>
uv run python manage.py geocode_counties
uv run python manage.py createsuperuser
```

## Development

Run the Django dev server and Tailwind watcher in separate terminals:

```bash
uv run python manage.py tailwind start
uv run python manage.py runserver
```

## Data

Petition data is imported from a CSV export of the LVA catalog. Geographic assignments use the spreadsheet's binary county columns to map petitions to modern counties across four states. The original `Locality` field is preserved but not used for geographic lookups, as historical county names often don't correspond to modern boundaries.
