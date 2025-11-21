from __future__ import annotations

import io
import json
from typing import List
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandParser
from django.contrib.gis.geos import Point

from transit_layer.models import MetrobusStation


def _open(path: str, encoding: str) -> io.TextIOBase:
    parsed = urlparse(path)
    if parsed.scheme in ("http", "https"):
        req = Request(path, headers={"User-Agent": "IstanbulPropTech/ingest"})
        resp = urlopen(req, timeout=60)
        data = resp.read()
        return io.StringIO(data.decode(encoding, errors="ignore"))
    return open(path, "r", encoding=encoding, errors="ignore")


class Command(BaseCommand):
    help = "Import Metrobus stations from a JSON array into transit_layer.MetrobusStation."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--path", required=True, help="JSON file path or URL")
        parser.add_argument("--encoding", default="utf-8", help="File encoding (default utf-8)")
        parser.add_argument("--name-field", default="station", help="Key for station name (e.g., 'station' or 'name')")
        parser.add_argument("--lat-field", default="lat", help="Key for latitude")
        parser.add_argument("--lon-field", default="long", help="Key for longitude (e.g., 'long' or 'lon')")
        parser.add_argument("--limit", type=int, default=0, help="Only import first N entries (testing)")
        parser.add_argument("--truncate", action="store_true", help="Delete existing MetrobusStation rows before import")

    def handle(self, *args, **opts):
        path = opts["path"]
        encoding = opts["encoding"]
        k_name = opts["name_field"]
        k_lat = opts["lat_field"]
        k_lon = opts["lon_field"]
        limit = opts["limit"]

        if opts.get("truncate"):
            deleted = MetrobusStation.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f"Truncated MetrobusStation table (deleted {deleted})"))

        try:
            fh = _open(path, encoding)
            data = json.load(fh)
        except Exception as e:
            self.stderr.write(f"Failed to read {path}: {e}")
            return 2

        if not isinstance(data, list):
            self.stderr.write("JSON must be an array of objects")
            return 3

        batch: List[MetrobusStation] = []
        created = 0
        total = 0

        for row in data:
            total += 1
            if limit and total > limit:
                break
            if not isinstance(row, dict):
                continue
            try:
                name = str(row.get(k_name, "")).strip() or "Metrobus Station"
                lat = float(str(row.get(k_lat, "")).strip())
                lon = float(str(row.get(k_lon, "")).strip())
            except Exception:
                continue
            batch.append(MetrobusStation(name=name, location=Point(lon, lat, srid=4326)))
            if len(batch) >= 1000:
                MetrobusStation.objects.bulk_create(batch, ignore_conflicts=True)
                created += len(batch)
                batch.clear()

        if batch:
            MetrobusStation.objects.bulk_create(batch, ignore_conflicts=True)
            created += len(batch)

        self.stdout.write(self.style.SUCCESS(f"Imported {created} metrobus stations from {path}"))

