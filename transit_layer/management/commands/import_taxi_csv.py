from __future__ import annotations

import csv
import io
from typing import List
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandParser
from django.contrib.gis.geos import Point

from transit_layer.models import TaxiStand


def _open(path: str, encoding: str) -> io.TextIOBase:
    parsed = urlparse(path)
    if parsed.scheme in ("http", "https"):
        req = Request(path, headers={"User-Agent": "IstanbulPropTech/ingest"})
        resp = urlopen(req, timeout=60)
        data = resp.read()
        return io.StringIO(data.decode(encoding, errors="ignore"))
    return open(path, "r", encoding=encoding, errors="ignore")


class Command(BaseCommand):
    help = "Import Taxi stands from CSV into transit_layer.TaxiStand."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--path", required=True, help="CSV path or URL")
        parser.add_argument("--encoding", default="utf-8", help="CSV encoding")
        parser.add_argument("--name-field", default="name", help="Column for stand name")
        parser.add_argument("--lat-field", default="lat", help="Column for latitude")
        parser.add_argument("--lon-field", default="lon", help="Column for longitude")
        parser.add_argument("--limit", type=int, default=0, help="Only first N rows (testing)")
        parser.add_argument("--truncate", action="store_true", help="Delete existing TaxiStand rows before import")

    def handle(self, *args, **opts):
        path = opts["path"]
        encoding = opts["encoding"]
        k_name = opts["name_field"]
        k_lat = opts["lat_field"]
        k_lon = opts["lon_field"]
        limit = opts["limit"]

        if opts.get("truncate"):
            deleted = TaxiStand.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f"Truncated TaxiStand ({deleted})"))

        try:
            fh = _open(path, encoding)
        except Exception as e:
            self.stderr.write(f"Failed to open {path}: {e}")
            return 2

        reader = csv.DictReader(fh)
        batch: List[TaxiStand] = []
        created = 0
        total = 0

        for row in reader:
            total += 1
            if limit and total > limit:
                break
            try:
                name = (row.get(k_name) or "Taxi Stand").strip()
                lat = float(str(row.get(k_lat, "")).strip())
                lon = float(str(row.get(k_lon, "")).strip())
            except Exception:
                continue
            batch.append(TaxiStand(name=name, location=Point(lon, lat, srid=4326)))
            if len(batch) >= 1000:
                TaxiStand.objects.bulk_create(batch, ignore_conflicts=True)
                created += len(batch)
                batch.clear()

        if batch:
            TaxiStand.objects.bulk_create(batch, ignore_conflicts=True)
            created += len(batch)

        self.stdout.write(self.style.SUCCESS(f"Imported {created} taxi stands from {path}"))

