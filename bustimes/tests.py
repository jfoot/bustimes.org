import os
from datetime import date, datetime, timedelta, timezone

from django.test import TestCase
from vcr import use_cassette

from busstops.models import DataSource, Service
from vehicles.models import Livery, Vehicle

from .models import Calendar, CalendarDate, Garage, Route, StopTime, Trip
from .utils import get_routes


class BusTimesTest(TestCase):
    def test_tfl_vehicle_view(self):
        DataSource.objects.create(id=7, name="London")
        Livery.objects.create(id=262, name="London", colours="#dc241f", published=True)
        Vehicle.objects.create(code="LTZ1243", reg="LTZ1243")

        with use_cassette(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "vcr", "tfl_vehicle.yaml"
            ),
            decode_compressed_response=True,
        ) as cassette:
            with self.assertNumQueries(5):
                response = self.client.get("/vehicles/tfl/LTZ1243")

            self.assertContains(response, "<h2>8 to Tottenham Court Road</h2>")
            self.assertContains(response, "<h2>LTZ 1243</h2>")
            self.assertContains(
                response,
                '<td class="stop-name">'
                '<a href="/stops/490010552N">Old Ford Road (OB)</a></td>',
            )
            self.assertContains(response, "<td>18:55</td>")
            self.assertContains(
                response,
                '<td class="stop-name"><a href="/stops/490004215M">Bow Church</a></td>',
            )

            response = self.client.get("/vehicles/tfl/LJ53NHP")
            self.assertEqual(response.status_code, 404)

            Vehicle.objects.create(code="LJ53NHP", reg="LJ53NHP")
            cassette.rewind()
            response = self.client.get("/vehicles/tfl/LJ53NHP")
            self.assertContains(response, "LJ53 NHP")

    def test_calendar(self):
        calendar = Calendar(
            mon=False,
            tue=False,
            wed=False,
            thu=False,
            fri=False,
            sat=False,
            sun=False,
            start_date=date(2021, 1, 3),
        )

        self.assertEqual("", str(calendar))

        calendar.wed = True
        calendar.thu = True
        calendar.fri = True
        self.assertEqual("Wednesday to Friday", str(calendar))

        calendar.wed = False
        calendar.thu = False
        calendar.fri = False
        calendar.mon = True
        self.assertEqual("Mondays", str(calendar))

        calendar.tue = True
        self.assertEqual("Mondays and Tuesdays", str(calendar))

        calendar.sat = True
        self.assertEqual("Mondays, Tuesdays and Saturdays", str(calendar))

        calendar.mon = False
        calendar.sat = False
        calendar.wed = True

        calendar.start_date = date(2020, 2, 5)
        calendar.end_date = date(2020, 2, 10)
        self.assertEqual("Tuesdays and Wednesdays", str(calendar))
        calendar.bank_holiday_exclusions = [date(2021, 1, 2)]
        calendar.bank_holiday_inclusions = []
        calendar.save()
        self.assertEqual(
            "Wednesday 5 February 2020 only", calendar.describe_for_timetable()
        )
        calendar.end_date = None
        self.assertEqual(
            "Tuesdays and Wednesdays",
            calendar.describe_for_timetable(),
        )
        calendar.bank_holiday_exclusions = [date(2021, 1, 5)]
        self.assertEqual(
            "Tuesdays and Wednesdays (not bank holidays)",
            calendar.describe_for_timetable(),
        )
        calendar.bank_holiday_inclusions = [date(2021, 1, 2)]
        calendar.bank_holiday_exclusions = []
        self.assertEqual(
            "Tuesdays and Wednesdays and bank holidays from Wednesday 5 February 2020",
            calendar.describe_for_timetable(date(2020, 1, 1)),
        )

        calendar.summary = "Toby Young School of Assholery days"
        self.assertEqual(
            "Tuesdays and Wednesdays, Toby Young School of Assholery days",
            str(calendar),
        )

        calendar.summary = ""
        calendar.tue = False
        calendar.wed = False
        calendar.sat = True
        calendar.start_date = date(
            2022, 6, 12
        )  # a Sunday – won't actually operate til Saturday...
        self.assertEqual(
            "Saturdays and bank holidays from Saturday 18 June 2022",
            calendar.describe_for_timetable(date(2022, 6, 10)),
        )
        self.assertEqual(
            "Saturdays and bank holidays",  # (from this Saturday, no need to specify)
            calendar.describe_for_timetable(date(2022, 6, 16)),
        )

        calendar.bank_holiday_inclusions = []
        calendar.mon = True
        calendar.tue = True
        calendar.wed = True
        calendar.thu = True
        calendar.fri = True
        calendar.end_date = date(2022, 7, 29)
        self.assertEqual(
            "Monday to Saturday until Friday 29 July 2022",
            calendar.describe_for_timetable(date(2022, 7, 20)),
        )

        calendar.save()
        CalendarDate.objects.create(
            start_date=date(2022, 7, 22),
            end_date=date(2022, 7, 22),
            operation=False,
            calendar=calendar,
        )
        CalendarDate.objects.create(
            start_date=date(2022, 7, 24),  # "and Sunday 24 July"
            end_date=date(2022, 7, 24),
            operation=True,
            calendar=calendar,
        )

        # calendar date outside calendar date range – should have no effect
        CalendarDate.objects.create(
            start_date=date(2022, 8, 28),
            end_date=date(2022, 8, 29),
            operation=False,
            calendar=calendar,
        )
        self.assertEqual(
            "Monday to Saturday (not Friday 22 July) (and Sunday 24 July) until Friday 29 July 2022",
            calendar.describe_for_timetable(date(2022, 7, 20)),
        )

    def test_trip(self):
        trip = Trip()

        trip.start = timedelta(hours=10, minutes=47, seconds=30)
        trip.end = timedelta(hours=11, minutes=00, seconds=00)
        self.assertEqual(
            trip.start_datetime(date(2021, 6, 20)),
            datetime(2021, 6, 20, 10, 47, 30, tzinfo=timezone(timedelta(hours=1))),
        )
        self.assertEqual(
            trip.end_datetime(date(2021, 6, 20)),
            datetime(2021, 6, 20, 11, tzinfo=timezone(timedelta(hours=1))),
        )
        self.assertEqual(
            trip.start_datetime(date(2021, 11, 1)),
            datetime(2021, 11, 1, 10, 47, 30, tzinfo=timezone(timedelta())),
        )

        trip.start = timedelta(hours=25, minutes=47, seconds=30)
        self.assertEqual(
            trip.start_datetime(date(2021, 6, 20)),
            datetime(2021, 6, 21, 1, 47, 30, tzinfo=timezone(timedelta(hours=1))),
        )
        self.assertEqual(
            trip.start_datetime(date(2021, 10, 31)),
            datetime(2021, 11, 1, 1, 47, 30, tzinfo=timezone(timedelta())),
        )

        self.assertEqual(str(trip), "01:47")

    def test_stop_time(self):
        time = StopTime(departure=timedelta(hours=10, minutes=47, seconds=30))
        self.assertEqual(str(time), "10:47")

        time.arrival = timedelta(hours=10, minutes=30, seconds=2)
        time.departure = None
        self.assertEqual(
            time.departure_or_arrival(), timedelta(hours=10, minutes=30, seconds=2)
        )

    def test_get_routes(self):
        sources = DataSource.objects.bulk_create(
            [
                DataSource(name="Lynx A", sha1="abc123"),
                DataSource(name="Lynx B", sha1="abc123"),
                DataSource(name="Leith Lynx"),
                DataSource(name="Ticketer", url=""),
            ]
        )
        service = Service.objects.create(line_name="55")

        routes = [
            Route(
                service=service,
                description="1",
                code="55",
                revision_number=3,
                source=sources[0],
            ),
            Route(
                service=service,
                description="2",
                revision_number=3,
                source=sources[1],
            ),
            Route(
                service=service,
                description="3",
                code="55b",
                revision_number=4,
                source=sources[0],
                start_date=date(2022, 4, 4),
                end_date=date(2022, 4, 4),
            ),
            Route(
                service=service,
                description="4",
                code="55c",
                revision_number=4,
                source=sources[0],
                start_date=date(2022, 4, 5),
            ),
            Route(
                service=service,
                description="5",
                code="55d",
                revision_number=5,
                source=sources[2],
            ),
            # Ticketer:
            Route(
                service=service,
                description="5B",
                service_code="PF0002189:81",
                code="KCTB_5B_KCTBPF0002189815B_20220113_-_1d735f37-ef5d-4b8c-b853-c418e6c48882.xml",
                revision_number=3,
                source=sources[3],
            ),
            Route(
                service=service,
                description="5BH",
                service_code="PF0002189:81",
                code="KCTB_5BH_KCTBPF0002189815B_20220113_-_b282207a-ed52-4cdf-a4e0-17f4bd6b7a55.xml",
                revision_number=5,
                source=sources[3],
            ),
        ]

        # maximum revision number
        self.assertEqual(get_routes(routes[:5], when=date(2022, 4, 4)), [routes[4]])

        # ignore duplicate source with the same sha1
        self.assertEqual(get_routes(routes[:2]), [routes[1]])

        # Ticketer filename - treat '5B' and '5BH' despite having the same service_code
        self.assertEqual(get_routes(routes[5:7]), routes[5:7])

        # from_date - include future versions
        self.assertEqual(
            get_routes(routes[2:4], from_date=date(2022, 4, 3)), routes[2:4]
        )
        self.assertEqual(
            get_routes(routes[2:4], from_date=date(2022, 4, 4)), routes[2:4]
        )
        # ignore old versions:
        self.assertEqual(
            get_routes(routes[2:4], from_date=date(2022, 4, 5)), routes[3:4]
        )

    def test_get_routes_tfl(self):
        source = DataSource(id=1, name="L")

        routes = [
            Route(
                id=1,
                code="86-683-_-y05-60196",
                revision_number=3,
                start_date=date(2023, 2, 11),
                source=source,
            ),
            Route(
                id=2,
                code="86-683-_-y05-60197",
                revision_number=3,
                start_date=date(2023, 2, 11),
                source=source,
            ),
            Route(
                id=3,
                code="86-683-_-y05-59862",
                revision_number=3,
                start_date=date(2023, 2, 11),
                source=source,
            ),
        ]

        gotten_routes = get_routes(routes)
        self.assertEqual(len(gotten_routes), 1)
        self.assertEqual(gotten_routes[0].code, "86-683-_-y05-60197")
        self.assertEqual(gotten_routes[0].id, 2)

    def test_garage(self):
        garage = Garage(code="LOW", name="LOWESTOFT TOWN")
        self.assertEqual(str(garage), "Lowestoft Town")
        garage.name = "LOW"
        self.assertEqual(str(garage), "LOW")
