import csv
from datetime import date

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from petitions.models import County, Petition, Subject

# Column index ranges (from the CSV header)
VA_COUNTY_START = 23
VA_COUNTY_END = 157  # exclusive; includes "Unknown" at 156
SUBJECT_START = 158
SUBJECT_END = 198  # exclusive; includes "Unknown" at 197
WV_COUNTY_START = 201
# WV goes to end of row

TYPE_MAP = {
    'Legislative petition': 'legislative',
    'Declaration for Revolutionary War pension': 'pension',
}


class Command(BaseCommand):
    help = 'Import petitions from the LVA CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', help='Path to the CSV file')
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear existing data before importing',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Petition.objects.all().delete()
            County.objects.all().delete()
            Subject.objects.all().delete()

        with open(options['csv_file'], newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)

            # Extract column names for counties and subjects
            va_county_cols = headers[VA_COUNTY_START:VA_COUNTY_END]
            subject_cols = headers[SUBJECT_START:SUBJECT_END]
            wv_county_cols = headers[WV_COUNTY_START:]

            # Pre-create county and subject records
            va_counties = self._ensure_counties(va_county_cols, 'VA')
            wv_counties = self._ensure_counties(wv_county_cols, 'WV')
            subjects = self._ensure_subjects(subject_cols)

            imported = 0
            skipped = 0
            for row in reader:
                if not row or not row[0].strip():
                    continue

                try:
                    serial = int(row[0])
                except ValueError:
                    skipped += 1
                    continue

                if Petition.objects.filter(serial=serial).exists():
                    skipped += 1
                    continue

                petition = self._create_petition(row, serial)
                self._assign_counties(petition, row, va_counties, va_county_cols,
                                      VA_COUNTY_START)
                self._assign_counties(petition, row, wv_counties, wv_county_cols,
                                      WV_COUNTY_START)
                self._assign_ky_pa_counties(petition, row)
                self._assign_subjects(petition, row, subjects, subject_cols,
                                      SUBJECT_START)
                imported += 1

            self.stdout.write(self.style.SUCCESS(
                f'Imported {imported} petitions, skipped {skipped}'
            ))

    def _ensure_counties(self, col_names, state):
        counties = {}
        for name in col_names:
            name = name.strip()
            if not name or name == 'Unknown':
                continue
            slug = slugify(f"{state}-{name}")
            county, _ = County.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'state': state},
            )
            counties[name] = county
        return counties

    def _ensure_subjects(self, col_names):
        subjects = {}
        for name in col_names:
            name = name.strip()
            if not name or name == 'Unknown':
                continue
            slug = slugify(name)
            subject, _ = Subject.objects.get_or_create(
                slug=slug,
                defaults={'name': name},
            )
            subjects[name] = subject
        return subjects

    def _create_petition(self, row, serial):
        parsed_date = None
        date_str = row[6].strip() if len(row) > 6 else ''
        if date_str:
            try:
                parts = date_str.split('-')
                parsed_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                pass

        raw_type = row[14].strip() if len(row) > 14 else ''
        petition_type = TYPE_MAP.get(raw_type, 'legislative')

        description = row[7].strip() if len(row) > 7 else ''
        # Strip the boilerplate that appears in every description
        boilerplate_marker = 'Petitions to the General Assembly were'
        if boilerplate_marker in description:
            description = description[:description.index(boilerplate_marker)].rstrip('; ')

        return Petition.objects.create(
            serial=serial,
            mms_id=row[1].strip() if len(row) > 1 else '',
            rosetta_ie=row[2].strip() if len(row) > 2 else '',
            title=row[3].strip() if len(row) > 3 else '',
            petition_type=petition_type,
            date=parsed_date,
            description=description,
            locality_raw=row[8].strip() if len(row) > 8 else '',
            permalink=row[13].strip() if len(row) > 13 else '',
        )

    def _assign_counties(self, petition, row, county_map, col_names, start_idx):
        for i, name in enumerate(col_names):
            name = name.strip()
            idx = start_idx + i
            if idx < len(row) and row[idx].strip().lower() == 'yes':
                county = county_map.get(name)
                if county:
                    petition.counties.add(county)

    def _assign_ky_pa_counties(self, petition, row):
        # KY_ModernLocality is column 19, PA is 20
        for col_idx, state in [(19, 'KY'), (20, 'PA')]:
            if col_idx >= len(row):
                continue
            value = row[col_idx].strip()
            if not value or value == 'Kentucky Counties':
                continue
            for name in value.split(';'):
                name = name.strip()
                if not name:
                    continue
                slug = slugify(f"{state}-{name}")
                county, _ = County.objects.get_or_create(
                    slug=slug,
                    defaults={'name': name, 'state': state},
                )
                petition.counties.add(county)

    def _assign_subjects(self, petition, row, subject_map, col_names, start_idx):
        for i, name in enumerate(col_names):
            name = name.strip()
            idx = start_idx + i
            if idx < len(row) and row[idx].strip().lower() == 'yes':
                subject = subject_map.get(name)
                if subject:
                    petition.subjects.add(subject)

        # Also parse the semicolon-delimited Subject column (index 15)
        if len(row) > 15:
            for subj_name in row[15].split(';'):
                subj_name = subj_name.strip()
                if subj_name and subj_name != 'Unknown':
                    subject = subject_map.get(subj_name)
                    if subject:
                        petition.subjects.add(subject)
