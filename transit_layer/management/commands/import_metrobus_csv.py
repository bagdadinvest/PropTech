from __future__ import annotations

import csv
import io
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
    help = "Import Metrobus stations from CSV into transit_layer.MetrobusStation."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--path", required=True, help="CSV file path or URL")
        parser.add_argument("--encoding", default="utf-8", help="CSV encoding (e.g., utf-8, latin-1)")
        parser.add_argument("--name-field", default="name", help="Column for station name (e.g., 'name' or 'DurakAdi')")
        parser.add_argument("--lat-field", default="lat", help="Column for latitude")
        parser.add_argument("--lon-field", default="lon", help="Column for longitude")
        parser.add_argument("--limit", type=int, default=0, help="Import only first N rows (testing)")
        parser.add_argument("--truncate", action="store_true", help="Delete existing MetrobusStation rows before import")

    def handle(self, *args, **opts):
        path = opts["path"]
        encoding = opts["encoding"]
        name_field = opts["name_field"]
        lat_field = opts["lat_field"]
        lon_field = opts["lon_field"]
        limit = opts["limit"]

        if opts.get("truncate"):
            deleted = MetrobusStation.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f"Truncated MetrobusStation table (deleted {deleted})"))

        try:
            fh = _open(path, encoding)
        except Exception as e:
            self.stderr.write(f"Failed to open {path}: {e}")
            return 2

        reader = csv.DictReader(fh)
        batch: List[MetrobusStation] = []
        total = 0
        created = 0

        for row in reader:
            total += 1
            if limit and total > limit:
                break
            try:
                name = str(row.get(name_field, "")).strip() or "Metrobus Station"
                lat = float(str(row.get(lat_field, "")).strip())
                lon = float(str(row.get(lon_field, "")).strip())
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

