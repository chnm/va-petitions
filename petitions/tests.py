import csv
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from . import lva
from .models import County, Petition, Subject


class LvaTransformTests(TestCase):
    def test_scalar_transforms_normalize_source_values(self):
        self.assertEqual(lva.parse_type(' Legislative petition '), 'legislative')
        self.assertEqual(lva.parse_type('unknown'), 'legislative')
        self.assertEqual(lva.parse_date('1820-03-04'), date(1820, 3, 4))
        self.assertIsNone(lva.parse_date('1820-99-04'))
        self.assertEqual(
            lva.clean_description(
                'Keep this; Petitions to the General Assembly were boilerplate'
            ),
            'Keep this',
        )


class ImportPetitionsCommandTests(TestCase):
    def test_import_uses_shared_transforms_and_assigns_all_relations(self):
        with TemporaryDirectory() as directory:
            csv_path = Path(directory) / 'petitions.csv'
            self._write_source_csv(csv_path)

            call_command('import_petitions', csv_path, verbosity=0)
            call_command('import_petitions', csv_path, verbosity=0)

        petition = Petition.objects.get(serial=101)
        self.assertEqual(petition.petition_type, 'pension')
        self.assertEqual(petition.date, date(1819, 2, 3))
        self.assertEqual(petition.description, 'A useful description')
        self.assertEqual(Petition.objects.count(), 1)
        self.assertSetEqual(
            set(petition.counties.values_list('state', 'name')),
            {
                ('VA', 'Accomack County'),
                ('WV', 'Ohio County'),
                ('KY', 'Fayette County'),
                ('PA', 'Allegheny County'),
            },
        )
        self.assertSetEqual(
            set(petition.subjects.values_list('name', flat=True)),
            {'Roads', 'Bridges'},
        )

    @staticmethod
    def _write_source_csv(path):
        headers = ['' for _ in range(202)]
        headers[0] = 'Serial'
        headers[1] = 'MMS ID'
        headers[2] = 'Rosetta IE'
        headers[3] = 'Title'
        headers[6] = 'Creation Date'
        headers[7] = 'Description'
        headers[8] = 'Locality'
        headers[13] = 'permalink'
        headers[14] = 'Type'
        headers[15] = 'Subject'
        headers[19] = 'KY_ModernLocality'
        headers[20] = 'PA_ModernLocality'
        headers[23] = 'Accomack County'
        headers[158] = 'Roads'
        headers[201] = 'Ohio County'

        values = ['' for _ in headers]
        values[0] = '101'
        values[1] = 'mms-101'
        values[2] = 'ie-101'
        values[3] = 'A petition title'
        values[6] = '1819-02-03'
        values[7] = (
            'A useful description; '
            'Petitions to the General Assembly were boilerplate'
        )
        values[8] = 'Accomack County'
        values[13] = 'https://example.com/petition/101'
        values[14] = 'Declaration for Revolutionary War pension'
        values[15] = 'Bridges'
        values[19] = 'Fayette County'
        values[20] = 'Allegheny County'
        values[23] = 'Yes'
        values[158] = 'Yes'
        values[201] = 'Yes'

        with path.open('w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headers)
            writer.writerow(values)


class PetitionViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.county = County.objects.create(
            name='Henrico County', slug='va-henrico-county', state='VA'
        )
        cls.subject = Subject.objects.create(name='Roads', slug='roads')
        cls.petition = Petition.objects.create(
            serial=1,
            title='Build a bridge',
            petition_type='legislative',
            date=date(1800, 1, 1),
            description='A road and bridge petition.',
        )
        cls.petition.counties.add(cls.county)
        cls.petition.subjects.add(cls.subject)

    def test_map_county_detail_honors_subject_and_year_filters(self):
        url = reverse('petitions:map_county_detail', args=[self.county.slug])

        response = self.client.get(
            url,
            {'subject': 'roads', 'from': '1799', 'to': '1801'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['title'], self.petition.title)

        response = self.client.get(url, {'from': 'not-a-year', 'to': '1799'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_catalog_handles_sparse_type_facets_and_an_invalid_sort(self):
        response = self.client.get(
            reverse('petitions:catalog'),
            {'sort': 'invalid'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.petition.title)
