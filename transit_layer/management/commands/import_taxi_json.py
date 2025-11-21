from __future__ import annotations

import io
import json
from typing import List, Any, Dict
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
    help = (
        "Import Taxi stands from a JSON file into transit_layer.TaxiStand. "
        "Supports either an array of objects with lat/lon or a GeoJSON FeatureCollection."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--path", required=True, help="JSON path or URL")
        parser.add_argument("--encoding", default="utf-8", help="File encoding")
        parser.add_argument("--name-field", default="name", help="Key for name (for array or GeoJSON properties)")
        parser.add_argument("--lat-field", default="lat", help="Key for latitude (array form only)")
        parser.add_argument("--lon-field", default="lon", help="Key for longitude (array form only)")
        parser.add_argument("--limit", type=int, default=0, help="First N only")
        parser.add_argument("--truncate", action="store_true", help="Delete existing rows before import")

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
            data: Any = json.load(fh)
        except Exception as e:
            self.stderr.write(f"Failed to read {path}: {e}")
            return 2

        batch: List[TaxiStand] = []
        created = 0
        total = 0

        def flush_batch():
            nonlocal created, batch
            if batch:
                TaxiStand.objects.bulk_create(batch, ignore_conflicts=True)
                created += len(batch)
                batch.clear()

        # Case 1: GeoJSON FeatureCollection
        if isinstance(data, dict) and data.get("type") == "FeatureCollection" and isinstance(data.get("features"), list):
            for feat in data["features"]:
                total += 1
                if limit and total > limit:
                    break
                try:
                    props: Dict[str, Any] = feat.get("properties") or {}
                    geom: Dict[str, Any] = feat.get("geometry") or {}
                    coords = (geom.get("coordinates") or [None, None])
                    lon = float(coords[0])
                    lat = float(coords[1])
                    name = (str(props.get(k_name, "")).strip()) or "Taxi Stand"
                except Exception:
                    continue
                batch.append(TaxiStand(name=name, location=Point(lon, lat, srid=4326)))
                if len(batch) >= 1000:
                    flush_batch()
            flush_batch()
            self.stdout.write(self.style.SUCCESS(f"Imported {created} taxi stands from GeoJSON: {path}"))
            return 0

        # Case 2: Simple array of objects
        if not isinstance(data, list):
            self.stderr.write("Unsupported JSON. Expected array or GeoJSON FeatureCollection.")
            return 3

        for row in data:
            total += 1
            if limit and total > limit:
                break
            if not isinstance(row, dict):
                continue
            try:
                name = (str(row.get(k_name, "")).strip()) or "Taxi Stand"
                lat = float(str(row.get(k_lat, "")).strip())
                lon = float(str(row.get(k_lon, "")).strip())
            except Exception:
                continue
            batch.append(TaxiStand(name=name, location=Point(lon, lat, srid=4326)))
            if len(batch) >= 1000:
                flush_batch()

        flush_batch()
        self.stdout.write(self.style.SUCCESS(f"Imported {created} taxi stands from {path}"))
        return 0
