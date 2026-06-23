"""Shared transforms for the LVA petitions spreadsheet.

Used by both the ``import_petitions`` management command (positional CSV
parsing for bulk/initial loads) and the django-import-export
``PetitionResource`` (admin uploads, edit-or-append keyed on Serial).
"""
from datetime import date as _date

from django.utils.text import slugify

from .models import County, Subject

TYPE_MAP = {
    'Legislative petition': 'legislative',
    'Declaration for Revolutionary War pension': 'pension',
}
BOILERPLATE_MARKER = 'Petitions to the General Assembly were'


def parse_type(raw):
    return TYPE_MAP.get((raw or '').strip(), 'legislative')


def parse_date(raw):
    raw = (raw or '').strip()
    if not raw:
        return None
    try:
        year, month, day = raw.split('-')
        return _date(int(year), int(month), int(day))
    except (ValueError, IndexError):
        return None


def clean_description(raw):
    """Drop the boilerplate paragraph that trails every description."""
    desc = (raw or '').strip()
    if BOILERPLATE_MARKER in desc:
        desc = desc[:desc.index(BOILERPLATE_MARKER)].rstrip('; ')
    return desc


def build_lookups():
    """Return (county_by_name, subject_by_name) for resolving relation columns.

    The binary 'Yes' columns name VA and WV counties; those two states never
    share a county name, so each resolves unambiguously by name. KY/PA counties
    arrive through the semicolon locality columns instead.
    """
    counties = {c.name: c for c in County.objects.filter(state__in=['VA', 'WV'])}
    subjects = {s.name: s for s in Subject.objects.all()}
    return counties, subjects


def assign_relations(petition, row, county_lookup, subject_lookup, *, replace):
    """Set a petition's counties/subjects from a spreadsheet row dict.

    Binary 'Yes' columns map to VA/WV counties and subjects by header name; the
    semicolon Subject and KY/PA locality columns are split. With ``replace``
    true (admin edits), existing relations are overwritten by the sheet;
    otherwise they are only added to.
    """
    counties, subjects = set(), set()

    for header, value in row.items():
        if not header or str(value).strip().lower() != 'yes':
            continue
        if header in county_lookup:
            counties.add(county_lookup[header])
        elif header in subject_lookup:
            subjects.add(subject_lookup[header])

    # Semicolon-delimited Subject column.
    for name in str(row.get('Subject') or '').split(';'):
        name = name.strip()
        if name and name != 'Unknown' and name in subject_lookup:
            subjects.add(subject_lookup[name])

    # KY/PA modern localities (semicolon-delimited); created if missing.
    for column, state in [('KY_ModernLocality', 'KY'), ('PA_ModernLocality', 'PA')]:
        raw = str(row.get(column) or '').strip()
        if not raw or raw == 'Kentucky Counties':
            continue
        for name in raw.split(';'):
            name = name.strip()
            if not name:
                continue
            county, _ = County.objects.get_or_create(
                slug=slugify(f'{state}-{name}'),
                defaults={'name': name, 'state': state},
            )
            counties.add(county)

    if replace:
        petition.counties.set(counties)
        petition.subjects.set(subjects)
    else:
        if counties:
            petition.counties.add(*counties)
        if subjects:
            petition.subjects.add(*subjects)
