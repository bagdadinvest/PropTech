from __future__ import annotations

import csv
import io
from typing import List, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandParser
from django.contrib.gis.geos import Point

from stores_layer.models import Mall, Park


def _open(path: str, encoding: str) -> io.TextIOBase:
    parsed = urlparse(path)
    if parsed.scheme in ("http", "https"):
        req = Request(path, headers={"User-Agent": "IstanbulPropTech/ingest"})
        resp = urlopen(req, timeout=60)
        data = resp.read()
        return io.StringIO(data.decode(encoding, errors="ignore"))
    return open(path, "r", encoding=encoding, errors="ignore")


def _kind_from_value(val: str) -> Optional[str]:
    v = (val or "").strip().lower()
    if not v:
        return None
    if "park" in v or v in {"park", "parks"}:
        return "park"
    if "mall" in v or v in {"avm", "malls", "mall"}:
        return "mall"
    return None


class Command(BaseCommand):
    help = "Import malls and parks from a CSV into stores_layer (Mall, Park)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--path", required=True, help="CSV file path or URL")
        parser.add_argument("--encoding", default="utf-8", help="CSV encoding (e.g., utf-8, latin-1)")
        parser.add_argument("--name-field", default="name", help="Column for name")
        parser.add_argument("--lat-field", default="lat", help="Column for latitude")
        parser.add_argument("--lon-field", default="lon", help="Column for longitude")
        parser.add_argument("--type-field", default="type", help="Column for type/category (e.g., mall/park)")
        parser.add_argument("--kind", choices=["mall", "park"], help="If set, import all rows as this kind")
        parser.add_argument("--limit", type=int, default=0, help="Import only first N rows (testing)")
        parser.add_argument("--truncate", action="store_true", help="Delete existing Mall/Park rows before import")

    def handle(self, *args, **opts):
        path = opts["path"]
        encoding = opts["encoding"]
        k_name = opts["name_field"]
        k_lat = opts["lat_field"]
        k_lon = opts["lon_field"]
        k_type = opts["type_field"]
        fixed_kind: Optional[str] = opts.get("kind")
        limit = opts["limit"]

        if opts.get("truncate"):
            dm = Mall.objects.all().delete()[0]
            dp = Park.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f"Truncated Mall ({dm}) and Park ({dp}) tables"))

        try:
            fh = _open(path, encoding)
        except Exception as e:
            self.stderr.write(f"Failed to open {path}: {e}")
            return 2

        reader = csv.DictReader(fh)

        malls: List[Mall] = []
        parks: List[Park] = []
        total = 0
        created_m = 0
        created_p = 0

        for row in reader:
            total += 1
            if limit and total > limit:
                break
            try:
                name = str(row.get(k_name, "")).strip() or "Unnamed"
                lat = float(str(row.get(k_lat, "")).strip())
                lon = float(str(row.get(k_lon, "")).strip())
            except Exception:
                continue

            kind = fixed_kind or _kind_from_value(str(row.get(k_type, "")))
            if kind == "mall":
                malls.append(Mall(name=name, location=Point(lon, lat, srid=4326)))
            elif kind == "park":
                parks.append(Park(name=name, location=Point(lon, lat, srid=4326)))
            else:
                # Unknown type; skip
                continue

            if len(malls) >= 1000:
                Mall.objects.bulk_create(malls, ignore_conflicts=True)
                created_m += len(malls)
                malls.clear()
            if len(parks) >= 1000:
                Park.objects.bulk_create(parks, ignore_conflicts=True)
                created_p += len(parks)
                parks.clear()

        if malls:
            Mall.objects.bulk_create(malls, ignore_conflicts=True)
            created_m += len(malls)
        if parks:
            Park.objects.bulk_create(parks, ignore_conflicts=True)
            created_p += len(parks)

        self.stdout.write(self.style.SUCCESS(f"Imported {created_m} malls and {created_p} parks from {path}"))

