import logging
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
import yaml
from ciso8601 import parse_datetime
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware

from busstops.models import AdminArea, DataSource, Locality, StopArea, StopPoint

logger = logging.getLogger(__name__)


def get_datetime(string):
    datetime = parse_datetime(string)
    if not datetime.tzinfo:
        return make_aware(datetime)
    return datetime


def get_point(element, atco_code):
    easting = element.findtext("Easting")
    northing = element.findtext("Northing")
    grid_type = element.findtext("GridType")

    if not easting:
        easting = element.findtext("Translation/Easting")
        northing = element.findtext("Translation/Northing")
        grid_type = element.findtext("Translation/GridType")
    if easting:
        match grid_type:
            case "ITM":
                srid = 2157
            case "IrishOS":
                if atco_code[0] == "8":
                    srid = 2157
                else:
                    # not actually in Ireland, must be a mistake
                    srid = 27700
            case "UKOS" | None:
                srid = 27700
        return GEOSGeometry(f"SRID={srid};POINT({easting} {northing})")

    lon = element.findtext("Translation/Longitude")
    lat = element.findtext("Translation/Latitude")
    if lat is not None and lon is not None:
        return GEOSGeometry(f"POINT({lon} {lat})")


class Command(BaseCommand):
    mapping = (
        ("Descriptor/CommonName", "common_name"),
        ("Descriptor/Landmark", "landmark"),
        ("Descriptor/Street", "street"),
        ("Descriptor/Indicator", "indicator"),
        ("Descriptor/Crossing", "crossing"),
        ("Place/Suburb", "suburb"),
        ("Place/Town", "town"),
        ("StopClassification/StopType", "stop_type"),
        ("StopClassification/OnStreet/Bus/BusStopType", "bus_stop_type"),
        ("StopClassification/OnStreet/Bus/TimingStatus", "timing_status"),
    )

    # dumb placeholders in the data that should be blank
    nothings = {
        "-",
        "--",
        "---",
        "Crossing not known",
        "Street not known",
        "Landmark not known",
        "Unknown",
        "*",
        "Data Unavailable",
        "N/A",
        "Tba",
        "type_undefined",
        "class_undefined",
    }

    def get_stop(self, element):
        atco_code = element.findtext("AtcoCode")

        modified_at = element.attrib.get("ModificationDateTime")
        if modified_at:
            modified_at = get_datetime(modified_at)

        if (
            atco_code in self.existing_stops
            and modified_at == self.existing_stops[atco_code].modified_at
            and atco_code not in self.overrides
        ):
            return

        created_at = get_datetime(element.attrib["CreationDateTime"])

        point = get_point(element.find("Place/Location"), atco_code)

        bearing = element.findtext(
            "StopClassification/OnStreet/Bus/MarkedPoint/Bearing/CompassPoint"
        )
        if bearing is None:
            bearing = element.findtext(
                "StopClassification/OnStreet/Bus/UnmarkedPoint/Bearing/CompassPoint"
            )
        if bearing is None:
            bearing = ""

        # a stop can be in multiple stop areas
        # we assume (dubiously) that it has no more than 1 active one
        stop_area = None
        for stop_area_ref in element.findall("StopAreas/StopAreaRef"):
            if stop_area_ref.attrib.get("Modification") != "delete":
                stop_area = stop_area_ref.text

        stop = StopPoint(
            atco_code=atco_code,
            naptan_code=element.findtext("NaptanCode") or element.findtext("PlateCode"),
            created_at=created_at,
            modified_at=modified_at,
            latlong=point,
            bearing=bearing,
            locality_id=element.findtext("Place/NptgLocalityRef"),
            admin_area_id=element.findtext("AdministrativeAreaRef"),
            stop_area_id=stop_area,
            active=element.attrib.get("Status", "active") == "active",
        )

        if stop.locality_id and stop.locality_id not in self.localities:
            logger.warning(f"{atco_code} locality {stop.locality_id} does not exist")
            stop.locality_id = None

        if atco_code.startswith(stop.admin_area_id):
            stop.admin_area = self.admin_areas.get(stop.admin_area_id)
            logger.info(f"{atco_code} {stop.admin_area}")

        for xml_path, key in self.mapping:
            value = element.findtext(xml_path, "")
            if value in self.nothings:
                value = ""
            setattr(stop, key, value)

        if stop.indicator == stop.naptan_code:
            stop.indicator = ""

        if atco_code in self.overrides:
            for key, value in self.overrides[atco_code].items():
                if key == "latlong":
                    value = GEOSGeometry(value)
                setattr(stop, key, value)

        if atco_code in self.existing_stops:
            self.stops_to_update.append(stop)
        else:
            self.stops_to_create.append(stop)

    def get_stop_area(self, element):
        stop_area_code = element.findtext("StopAreaCode")

        point = get_point(element.find("Location"), stop_area_code)

        return StopArea(
            id=stop_area_code,
            name=element.findtext("Name"),
            latlong=point,
            active=element.attrib.get("Status", "active") == "active",
            admin_area_id=element.findtext("AdministrativeAreaRef"),
            stop_area_type=element.findtext("StopAreaType"),
        )

    bulk_update_fields = [
        "created_at",
        "modified_at",
        "naptan_code",
        "latlong",
        "bearing",
        "common_name",
        "landmark",
        "street",
        "crossing",
        "stop_type",
        "bus_stop_type",
        "timing_status",
        "locality",
        "admin_area",
        "stop_area",
        "indicator",
        "suburb",
        "town",
        "active",
    ]

    def download(self, source):
        url = "https://naptan.api.dft.gov.uk/v1/access-nodes"
        params = {"dataFormat": "xml"}

        return requests.get(url, params, timeout=60, stream=True)

    def update_and_create(self):
        # create any new stop areas
        stops = [stop for stop in self.stops_to_create if stop.stop_area_id]
        stops += [stop for stop in self.stops_to_update if stop.stop_area_id]

        existing_stop_areas = StopArea.objects.in_bulk(self.stop_areas.keys())
        stop_areas_to_update = []
        stop_areas_to_create = []
        for stop_area_id, stop_area in self.stop_areas.items():
            if stop_area_id in existing_stop_areas:
                stop_areas_to_update.append(stop_area)
            else:
                stop_areas_to_create.append(stop_area)

        StopArea.objects.bulk_create(stop_areas_to_create, batch_size=100)
        StopArea.objects.bulk_update(
            stop_areas_to_update,
            ["name", "latlong", "active", "admin_area", "stop_area_type"],
            batch_size=100,
        )

        existing_stop_areas = StopArea.objects.in_bulk(
            [stop.stop_area_id for stop in stops]
        )
        stop_areas_to_create = set(
            StopArea(
                id=stop.stop_area_id, active=True, admin_area_id=stop.admin_area_id
            )
            for stop in stops
            if stop.stop_area_id not in existing_stop_areas
        )
        StopArea.objects.bulk_create(stop_areas_to_create, batch_size=100)

        # create new stops
        StopPoint.objects.bulk_create(self.stops_to_create, batch_size=100)
        self.stops_to_create = []

        # update updated stops
        StopPoint.objects.bulk_update(
            self.stops_to_update, self.bulk_update_fields, batch_size=100
        )
        self.stops_to_update = []

    @staticmethod
    def add_arguments(parser):
        parser.add_argument("filename", nargs="?", type=str)

    def handle(self, *args, **options):
        source, created = DataSource.objects.get_or_create(name="NaPTAN")

        if options["filename"]:
            path = Path(options["filename"])
        else:
            path = settings.DATA_DIR / "naptan.xml"

            # download new data if there is any
            response = self.download(source)
            if response:
                with path.open("wb") as open_file:
                    for chunk in response.iter_content(chunk_size=102400):
                        open_file.write(chunk)

        # set up overrides/corrections
        overrides_path = settings.BASE_DIR / "fixtures" / "stops.yaml"
        with overrides_path.open() as open_file:
            self.overrides = yaml.load(open_file, yaml.BaseLoader)

        self.stops_to_create = []
        self.stops_to_update = []
        self.admin_areas = {
            admin_area.atco_code: admin_area
            for admin_area in AdminArea.objects.order_by()
        }
        self.localities = set(
            locality["pk"] for locality in Locality.objects.values("pk").order_by()
        )
        atco_code_prefix = None

        self.stop_areas = {}

        iterator = ET.iterparse(path, events=["start", "end"])
        for event, element in iterator:
            if event == "start":
                if element.tag == "{http://www.naptan.org.uk/}NaPTAN":
                    modified_at = get_datetime(element.attrib["ModificationDateTime"])
                    if modified_at == source.datetime:
                        return

                    source.datetime = modified_at

                continue

            element.tag = element.tag.removeprefix("{http://www.naptan.org.uk/}")
            if element.tag == "StopPoint":
                atco_code = element.findtext("AtcoCode")
                if atco_code[:3] != atco_code_prefix:
                    if atco_code_prefix:
                        self.update_and_create()

                    atco_code_prefix = atco_code[:3]

                    self.existing_stops = (
                        StopPoint.objects.only("atco_code", "modified_at")
                        .filter(atco_code__startswith=atco_code_prefix)
                        .order_by()
                        .in_bulk()
                    )

                self.get_stop(element)

                element.clear()  # save memory

            elif element.tag == "StopArea":
                stop_area = self.get_stop_area(element)
                self.stop_areas[stop_area.id] = stop_area
                element.clear()

        self.update_and_create()

        if not options["filename"]:
            source.save(update_fields=["datetime"])
