import csv

from django.core.management.base import BaseCommand

from petitions import lva
from petitions.models import County, Petition, Subject


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

        with open(
            options['csv_file'],
            newline='',
            encoding='utf-8-sig',
        ) as csv_file:
            reader = csv.DictReader(csv_file)
            if reader.fieldnames is None:
                self.stdout.write(self.style.WARNING('The CSV file is empty.'))
                return

            lva.ensure_counties_and_subjects(reader.fieldnames)
            county_lookup, subject_lookup = lva.build_lookups()

            imported = 0
            skipped = 0
            for row in reader:
                serial = self._parse_serial(row.get('Serial'))
                if serial is None or Petition.objects.filter(serial=serial).exists():
                    skipped += 1
                    continue

                petition = Petition.objects.create(
                    serial=serial,
                    mms_id=self._value(row, 'MMS ID'),
                    rosetta_ie=self._value(row, 'Rosetta IE'),
                    title=self._value(row, 'Title'),
                    petition_type=lva.parse_type(row.get('Type')),
                    date=lva.parse_date(row.get('Creation Date')),
                    description=lva.clean_description(row.get('Description')),
                    locality_raw=self._value(row, 'Locality'),
                    permalink=self._value(row, 'permalink'),
                )
                lva.assign_relations(
                    petition,
                    row,
                    county_lookup,
                    subject_lookup,
                    replace=False,
                )
                imported += 1

        self.stdout.write(self.style.SUCCESS(
            f'Imported {imported} petitions, skipped {skipped}'
        ))

    @staticmethod
    def _parse_serial(raw):
        try:
            return int(str(raw or '').strip())
        except ValueError:
            return None

    @staticmethod
    def _value(row, column):
        return str(row.get(column) or '').strip()
