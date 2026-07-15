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
                'Keep petitioner&#39;s claim &amp; loss; '
                'Petitions to the General Assembly were boilerplate'
            ),
            "Keep petitioner's claim & loss",
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
            locality_raw='Henrico County',
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

    def test_map_includes_locality_sort_and_help_dialog(self):
        response = self.client.get(reverse('petitions:map'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="locality-sort"')
        self.assertContains(response, 'site-select', count=2)
        self.assertContains(response, 'Record count')
        self.assertContains(response, 'Locality A&ndash;Z')
        self.assertContains(response, 'id="map-help-dialog"')
        self.assertContains(response, 'How to Use This Map')

    def test_catalog_handles_sparse_type_facets_and_an_invalid_sort(self):
        response = self.client.get(
            reverse('petitions:catalog'),
            {'sort': 'invalid'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.petition.title)
        self.assertContains(response, 'site-select', count=2)

    def test_catalog_rows_link_when_available_and_label_unavailable_files(self):
        available = Petition.objects.create(
            serial=2,
            title='A petition with an online file',
            petition_type='legislative',
            date=date(1801, 1, 1),
            permalink='https://example.com/petition/2',
        )

        response = self.client.get(reverse('petitions:catalog'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-catalog-row="available"')
        self.assertContains(response, f'href="{available.permalink}"')
        self.assertContains(response, 'data-catalog-row="unavailable"')
        self.assertContains(response, 'Coming Soon')
        self.assertNotContains(response, 'View &rarr;')

    def test_catalog_navigation_returns_to_results(self):
        response = self.client.get(reverse('petitions:catalog'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="catalog-results"')
        self.assertContains(response, '#catalog-results')

    def test_search_matches_words_in_any_order_and_ignores_query_glue(self):
        francisco = Petition.objects.create(
            serial=3,
            title='Francisco, Peter: Declaration for Revolutionary War Pension',
            petition_type='pension',
            date=date(1837, 1, 1),
        )

        for query in ('Peter Francisco', 'records for Peter Francisco'):
            with self.subTest(query=query):
                response = self.client.get(
                    reverse('petitions:search'),
                    {'q': query},
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, francisco.title)

    def test_search_includes_years_and_filter_dropdowns(self):
        response = self.client.get(
            reverse('petitions:search'),
            {'q': '1800'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.petition.title)
        self.assertContains(response, 'Narrow search')
        self.assertContains(response, 'id="search-subject"')
        self.assertContains(response, 'id="search-locality"')

    def test_search_filters_by_subject_and_locality_without_terms(self):
        response = self.client.get(
            reverse('petitions:search'),
            {'subject': self.subject.slug, 'loc': 'Henrico County'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.petition.title)
        self.assertContains(response, 'value="roads" selected')
        self.assertContains(response, 'value="Henrico County" selected')

    def test_search_rows_link_when_available_and_label_unavailable_files(self):
        available = Petition.objects.create(
            serial=4,
            title='A bridge record with an online file',
            petition_type='legislative',
            date=date(1802, 1, 1),
            permalink='https://example.com/catalog/4',
        )

        response = self.client.get(
            reverse('petitions:search'),
            {'q': 'bridge'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-search-row="available"')
        self.assertContains(response, f'href="{available.permalink}"')
        self.assertContains(response, 'data-search-row="unavailable"')
        self.assertContains(response, 'Coming Soon')
        self.assertNotContains(response, 'Open in the Catalogue')
        self.assertNotContains(response, 'Online catalog &rarr;')

    def test_petition_detail_routes_digitized_access_through_catalog(self):
        self.petition.rosetta_ie = 'IE123'
        self.petition.permalink = 'https://example.com/catalog/1'
        self.petition.save(update_fields=['rosetta_ie', 'permalink'])

        response = self.client.get(
            reverse('petitions:petition_detail', args=[self.petition.serial])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.petition.permalink)
        self.assertContains(response, 'View in the online catalog')
        self.assertNotContains(response, 'rosetta.virginiamemory.com')
