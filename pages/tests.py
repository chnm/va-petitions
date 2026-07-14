from django.test import TestCase
from django.urls import reverse

from petitions.models import Petition

from .models import Essay


class EssayLinkTests(TestCase):
    def test_rosetta_links_resolve_through_catalog_permalinks(self):
        Petition.objects.create(
            serial=1,
            title='A petition',
            petition_type='legislative',
            rosetta_ie='IE123',
            permalink='https://example.com/online-catalog/1',
        )
        essay = Essay.objects.create(
            title='An essay',
            body=(
                '[View at Virginia Memory]('
                'https://rosetta.virginiamemory.com/delivery/'
                'DeliveryManagerServlet?dps_pid=IE123)'
            ),
        )

        rendered = str(essay.body_html())

        self.assertIn('https://example.com/online-catalog/1', rendered)
        self.assertIn('View at the online catalog', rendered)
        self.assertNotIn('rosetta.virginiamemory.com', rendered)

    def test_unmatched_rosetta_link_is_not_rendered_as_a_dead_link(self):
        essay = Essay.objects.create(
            title='An essay',
            body=(
                '[View at Virginia Memory]('
                'https://rosetta.virginiamemory.com/delivery/'
                'DeliveryManagerServlet?dps_pid=IE999)'
            ),
        )

        rendered = str(essay.body_html())

        self.assertIn('View at the online catalog', rendered)
        self.assertNotIn('<a href=', rendered)
        self.assertNotIn('rosetta.virginiamemory.com', rendered)


class HomeStatsTests(TestCase):
    def test_navigation_about_link_targets_homepage_section(self):
        response = self.client.get(reverse('pages:introduction'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/#about"')
        self.assertNotContains(response, 'href="//#about"')

    def test_named_localities_split_compound_values_and_exclude_unknown(self):
        for serial, locality in enumerate(
            [
                'Accomack County; Northampton County',
                'Accomack County',
                'Unknown',
                '',
            ],
            start=1,
        ):
            Petition.objects.create(
                serial=serial,
                title=f'Record {serial}',
                petition_type='legislative',
                locality_raw=locality,
            )

        response = self.client.get(reverse('pages:home'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['locality_count'], 2)
        self.assertContains(response, 'Named Localities')

    def test_home_hero_features_a_catalogued_document_image(self):
        response = self.client.get(reverse('pages:home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'dissenters-petition-1776.webp')
        self.assertContains(
            response,
            'alma9917811905405756',
        )
        self.assertContains(response, 'First page of a handwritten 1776 petition')
