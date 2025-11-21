from __future__ import annotations

import csv
import io
import sys
from typing import Iterable, List
from urllib.parse import urlparse
from urllib.request import urlopen, Request

from django.core.management.base import BaseCommand, CommandParser
from django.contrib.gis.geos import Point

from transit_layer.models import BusStop


def _open_path(path: str, encoding: str) -> io.TextIOBase:
    parsed = urlparse(path)
    if parsed.scheme in ("http", "https"):
        req = Request(path, headers={"User-Agent": "IstanbulPropTech/ingest"})
        resp = urlopen(req, timeout=60)
        data = resp.read()
        return io.StringIO(data.decode(encoding))
    # local file
    return open(path, "r", encoding=encoding)


class Command(BaseCommand):
    help = "Import bus stops from a CSV (IMM Open Data) into transit_layer.BusStop."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--path", required=True, help="CSV filepath or URL")
        parser.add_argument("--encoding", default="utf-8", help="CSV encoding (default utf-8)")
        parser.add_argument("--name-field", default="stop_name", help="Column name for stop name")
        parser.add_argument("--lat-field", default="stop_lat", help="Column name for latitude")
        parser.add_argument("--lon-field", default="stop_lon", help="Column name for longitude")
        parser.add_argument("--limit", type=int, default=0, help="Limit rows for testing (0 = no limit)")
        parser.add_argument("--truncate", action="store_true", help="Delete existing BusStop rows before import")

    def handle(self, *args, **opts):
        path: str = opts["path"]
        encoding: str = opts["encoding"]
        name_field: str = opts["name_field"]
        lat_field: str = opts["lat_field"]
        lon_field: str = opts["lon_field"]
        limit: int = opts["limit"]

        if opts.get("truncate"):
            deleted = BusStop.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f"Truncated BusStop table (deleted {deleted})"))

        try:
            fh = _open_path(path, encoding)
        except Exception as e:
            self.stderr.write(f"Failed to open {path}: {e}")
            return 2

        reader = csv.DictReader(fh)
        batch: List[BusStop] = []
        total = 0
        created_total = 0

        for row in reader:
            total += 1
            if limit and total > limit:
                break
            try:
                name = str(row.get(name_field, "")).strip()
                lat = float(str(row.get(lat_field, "")).strip())
                lon = float(str(row.get(lon_field, "")).strip())
            except Exception:
                continue
            batch.append(BusStop(name=name or "Bus Stop", location=Point(lon, lat, srid=4326)))
            if len(batch) >= 1000:
                BusStop.objects.bulk_create(batch, ignore_conflicts=True)
                created_total += len(batch)
                batch.clear()

        if batch:
            BusStop.objects.bulk_create(batch, ignore_conflicts=True)
            created_total += len(batch)

        self.stdout.write(self.style.SUCCESS(f"Imported {created_total} bus stops from {path}"))

