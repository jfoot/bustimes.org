from django.contrib.gis.geos import Point
from busstops.models import Service
from ...models import Vehicle, VehicleLocation, VehicleJourney
from ..import_live_vehicles import ImportLiveVehiclesCommand


class Command(ImportLiveVehiclesCommand):
    source_name = 'transdevblazefield'
    url = 'https://transdevblazefield.arcticapi.com/network/vehicles'
    operators = {
        'YCD': 'YCST',
        'LUI': 'LNUD',
        'BPT': 'BPTR',
        'HDT': 'HRGT',
        'KDT': 'KDTR',
        'ROS': 'ROST'
    }

    def get_items(self):
        return super().get_items()['features']

    @classmethod
    def get_service(cls, operator, item):
        line_name = item['properties']['line']
        if operator == 'BLAC' and line_name == 'PRM':
            line_name = '1'
        services = Service.objects.filter(current=True, operator=operator, line_name=line_name)
        try:
            return services.get()
        except (Service.DoesNotExist, Service.MultipleObjectsReturned) as e:
            print(operator, line_name, e)

    def get_journey(self, item):
        journey = VehicleJourney()

        fleet_number = item['properties']['vehicle']
        if '-' in fleet_number:
            operator, fleet_number = item['properties']['vehicle'].split('-', 1)
        else:
            operator = item['_embedded']['transmodel:line']['id'].split(':')[0]

        operator = self.operators[operator]

        defaults = {
            'source': self.source,
            'operator_id': operator,
            'code': fleet_number
        }

        if ' - ' in fleet_number:
            fleet_number, defaults['reg'] = fleet_number.split(' - ')

        journey.service = self.get_service(operator, item)

        journey.vehicle, vehicle_created = Vehicle.objects.get_or_create(
            defaults,
            fleet_number=fleet_number,
            operator__in=self.operators.values()
        )

        return journey, vehicle_created

    def create_vehicle_location(self, item):
        return VehicleLocation(
            latlong=Point(item['geometry']['coordinates']),
            heading=item['properties'].get('bearing')
        )
