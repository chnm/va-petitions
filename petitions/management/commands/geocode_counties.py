import time

from django.core.management.base import BaseCommand
from geopy.geocoders import Nominatim

from petitions.models import County

STATE_NAMES = {
    'VA': 'Virginia',
    'WV': 'West Virginia',
    'KY': 'Kentucky',
    'PA': 'Pennsylvania',
}


class Command(BaseCommand):
    help = 'Geocode counties that are missing lat/lng using Nominatim'

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite', action='store_true',
            help='Overwrite existing coordinates',
        )

    def handle(self, *args, **options):
        geolocator = Nominatim(user_agent='va-petitions-dev')

        counties = County.objects.all()
        if not options['overwrite']:
            counties = counties.filter(latitude__isnull=True)

        total = counties.count()
        self.stdout.write(f'Geocoding {total} counties...')

        success = 0
        failed = []
        for i, county in enumerate(counties, 1):
            state_name = STATE_NAMES.get(county.state, county.state)
            # Try with "County" in the name for specificity
            query = f"{county.name}, {state_name}, USA"
            try:
                location = geolocator.geocode(query)
                if location:
                    county.latitude = location.latitude
                    county.longitude = location.longitude
                    county.save(update_fields=['latitude', 'longitude'])
                    success += 1
                else:
                    failed.append(query)
                    self.stdout.write(self.style.WARNING(f'  Not found: {query}'))
            except Exception as e:
                failed.append(query)
                self.stdout.write(self.style.ERROR(f'  Error for {query}: {e}'))

            if i % 20 == 0:
                self.stdout.write(f'  {i}/{total}...')

            # Nominatim usage policy: max 1 request/second
            time.sleep(1.1)

        self.stdout.write(self.style.SUCCESS(
            f'Done: {success} geocoded, {len(failed)} failed'
        ))
        if failed:
            self.stdout.write('Failed queries:')
            for q in failed:
                self.stdout.write(f'  {q}')
