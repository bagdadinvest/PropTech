import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point

from transit_layer.models import MetroStation


def _lower_keys(d: Dict[str, Any]) -> Dict[str, Any]:
    return {str(k).lower(): v for k, v in d.items()}


def _detect_name_key(cols: Iterable[str]) -> Optional[str]:
    candidates = [
        "name",
        "adi",
        "istasyon_adi",
        "ist_adi",
        "istasyon adı",
        "istasyon adi",
        "adi_istasyon",
        "istasyon",
    ]
    low = [c.lower() for c in cols]
    for cand in candidates:
        if cand in low:
            return cand
    return None


def _detect_lon_lat_keys(cols: Iterable[str]) -> Optional[Tuple[str, str]]:
    lon_candidates = ["lon", "longitude", "x", "boylam", "long", "lng"]
    lat_candidates = ["lat", "latitude", "y", "enlem"]
    low = [c.lower() for c in cols]
    lon_key = next((c for c in lon_candidates if c in low), None)
    lat_key = next((c for c in lat_candidates if c in low), None)
    if lon_key and lat_key:
        return lon_key, lat_key
    return None


class Command(BaseCommand):
    help = (
        "Load Metro rail stations into MetroStation from a CSV or GeoJSON file.\n"
        "Usage: python manage.py load_rail_data --file path/to/file.(csv|geojson)\n"
        "If no --file is provided, looks under <BASE_DIR>/data for a suitable file."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--file", dest="file", default=None, help="Path to CSV/GeoJSON file"
        )
        parser.add_argument(
            "--truncate",
            action="store_true",
            help="Delete all existing MetroStation records before import",
        )

    def handle(self, *args, **options):
        file_path: Optional[str] = options.get("file")
        truncate: bool = options.get("truncate", False)

        if not file_path:
            data_dir = Path(settings.BASE_DIR) / "data"
            if not data_dir.exists():
                raise CommandError(
                    f"No --file provided and data dir not found: {data_dir}. Place the IBB file there or pass --file."
                )
            # Prefer a GeoJSON if present, else CSV
            candidates = list(data_dir.glob("*rayli*istasyon*.geojson")) or list(
                data_dir.glob("*rayli*istasyon*.csv")
            )
            if not candidates:
                raise CommandError(
                    f"No candidate files found in {data_dir}. Provide --file explicitly."
                )
            file_path = str(candidates[0])

        file_path = os.path.abspath(file_path)
        if not os.path.exists(file_path):
            raise CommandError(f"File does not exist: {file_path}")

        if truncate:
            self.stdout.write("Truncating MetroStation table…")
            MetroStation.objects.all().delete()

        ext = Path(file_path).suffix.lower()
        created = 0
        updated = 0

        if ext in (".geojson", ".json"):
            created, updated = self._load_geojson(file_path)
        elif ext == ".csv":
            created, updated = self._load_csv(file_path)
        else:
            raise CommandError(
                f"Unsupported file extension '{ext}'. Use .csv or .geojson"
            )

        self.stdout.write(self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}"))

    def _load_geojson(self, path: str) -> Tuple[int, int]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        features: List[Dict[str, Any]] = data.get("features", [])
        created = 0
        updated = 0
        for feat in features:
            props = _lower_keys(feat.get("properties", {}))
            geom = feat.get("geometry") or {}
            if not geom or geom.get("type") != "Point":
                # Skip non-points
                continue
            coords = geom.get("coordinates")
            if not coords or len(coords) < 2:
                continue
            lon, lat = float(coords[0]), float(coords[1])
            name_key = _detect_name_key(props.keys()) or "name"
            name = str(props.get(name_key) or props.get("name") or "").strip()
            if not name:
                # As a fallback, synthesize a name from coordinates
                name = f"Station {lat:.5f},{lon:.5f}"

            obj, was_created = MetroStation.objects.update_or_create(
                name=name, defaults={"location": Point(lon, lat, srid=4326)}
            )
            if was_created:
                created += 1
            else:
                updated += 1
        return created, updated

    def _load_csv(self, path: str) -> Tuple[int, int]:
        # Try pandas first, fall back to csv module
        rows: List[Dict[str, Any]] = []
        try:
            import pandas as pd  # type: ignore

            df = pd.read_csv(path)
            rows = df.to_dict(orient="records")  # type: ignore[assignment]
        except Exception:  # pragma: no cover - lightweight fallback
            import csv

            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    rows.append(dict(r))

        created = 0
        updated = 0
        if not rows:
            return created, updated

        sample = _lower_keys(rows[0])
        name_key = _detect_name_key(sample.keys()) or "name"
        lon_lat = _detect_lon_lat_keys(sample.keys())

        if not lon_lat and "geometry" in sample:
            # Support WKT-like "POINT (lon lat)" in a geometry column
            lon_lat = ("geometry", "geometry")

        for r in rows:
            rr = _lower_keys(r)
            name = str(rr.get(name_key) or rr.get("name") or "").strip()
            if not name:
                continue

            lon: Optional[float] = None
            lat: Optional[float] = None

            if lon_lat and lon_lat[0] == lon_lat[1] == "geometry":
                geom_txt = str(rr.get("geometry") or "").strip()
                # Expect format like "POINT (28.971 41.011)"
                if geom_txt.upper().startswith("POINT"):
                    try:
                        inside = geom_txt.split("(", 1)[1].split(")", 1)[0]
                        parts = inside.replace(",", " ").split()
                        if len(parts) >= 2:
                            lon = float(parts[0])
                            lat = float(parts[1])
                    except Exception:
                        pass
            elif lon_lat:
                lon = float(str(rr.get(lon_lat[0]) or "0").replace(",", "."))
                lat = float(str(rr.get(lon_lat[1]) or "0").replace(",", "."))

            if lon is None or lat is None:
                continue

            obj, was_created = MetroStation.objects.update_or_create(
                name=name, defaults={"location": Point(lon, lat, srid=4326)}
            )
            if was_created:
                created += 1
            else:
                updated += 1

        return created, updated

