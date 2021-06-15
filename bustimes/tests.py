import os
from vcr import use_cassette
from django.test import TestCase
from busstops.models import DataSource
from vehicles.models import Livery


class BusTimesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        DataSource.objects.create(id=7, name='London')
        Livery.objects.create(id=262, name='London', colours='#dc241f')

    def test_tfl_vehicle_view(self):
        with use_cassette(
            os.path.join(
                 os.path.dirname(os.path.abspath(__file__)),
                 'vcr',
                'tfl_vehicle.yaml'
            ),
            decode_compressed_response=True
        ):
            with self.assertNumQueries(3):
                response = self.client.get('/vehicles/tfl/LTZ1243')
            vehicle = response.context["object"]

            self.assertContains(response, '<h2>8 to Tottenham Court Road</h2>')
            self.assertContains(response, f'<p><a href="/vehicles/{vehicle.id}">LTZ 1243</a></p>')
            self.assertContains(response, '<td><a href="/stops/490010552N">Old Ford Road (OB)</a></td>')
            self.assertContains(response, '<td>18:55</td>')
            self.assertContains(response, '<td><a href="/stops/490004215M">Bow Church</a></td>')

            response = self.client.get('/vehicles/tfl/LJ53NHP')
            self.assertEqual(response.status_code, 404)
