import csv
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from education_layer.models import Preschool


TARGET_DISTRICTS = ["Beşiktaş", "Kadıköy", "Sarıyer"]


@dataclass
class PreschoolRow:
    name: str
    district: str
    lat: float
    lon: float


def read_csv(path: Path) -> Optional[List[PreschoolRow]]:
    if not path.exists():
        return None
    rows: List[PreschoolRow] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            name = (r.get("name") or "").strip()
            district = (r.get("district") or "").strip()
            lat_str = (r.get("lat") or r.get("latitude") or "").strip()
            lon_str = (r.get("lon") or r.get("lng") or r.get("longitude") or "").strip()
            if not (name and district and lat_str and lon_str):
                continue
            try:
                lat = float(lat_str)
                lon = float(lon_str)
            except ValueError:
                continue
            rows.append(PreschoolRow(name=name, district=district, lat=lat, lon=lon))
    return rows or None


# Tiny offline seed so the command runs without network; recommended to supply CSV for ~50 entries.
DEFAULT_SEED: List[PreschoolRow] = [
    PreschoolRow(name="ABC Montessori", district="Beşiktaş", lat=41.0695, lon=29.0193),
    PreschoolRow(name="Kadıköy Kids Academy", district="Kadıköy", lat=40.9868, lon=29.0368),
    PreschoolRow(name="Sarıyer Preschool", district="Sarıyer", lat=41.1709, lon=29.0484),
]


class Command(BaseCommand):
    help = (
        "Discover and load private preschools/kindergartens across Beşiktaş, Kadıköy, Sarıyer.\n"
        "Options:\n"
        "- Read <BASE_DIR>/data/preschools.csv (name,district,lat,lon) if present.\n"
        "- Otherwise, query Nominatim for queries like 'Montessori', 'Anaokulu', 'Preschool' per district.\n"
        "- Aim to collect ~50 reputable entries total; de-duplicate by name+district."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument("--dry-run", action="store_true", help="Print results without writing to DB")
        parser.add_argument("--overwrite", action="store_true", help="Overwrite existing entries by name+district")
        parser.add_argument("--limit", type=int, default=50, help="Target total number of preschools (~50)")
        parser.add_argument("--csv", type=str, default="", help="Path to CSV (name,district,lat,lon)")

    def handle(self, *args, **options):
        dry = options.get("dry_run", False)
        overwrite = options.get("overwrite", False)
        target_total: int = max(1, int(options.get("limit") or 50))
        csv_path = Path(options.get("csv") or "")

        data_dir = Path(settings.BASE_DIR) / "data"
        default_csv = data_dir / "preschools.csv"

        rows = read_csv(csv_path) if csv_path else None
        if rows is None:
            rows = read_csv(default_csv)

        use_network = False
        if rows is None:
            # Fallback to network-based discovery via Nominatim if available
            try:
                from geopy.geocoders import Nominatim  # type: ignore
                geolocator = Nominatim(user_agent="istanbul_proptech_edu_preschool")
                use_network = True
            except Exception:
                # Last resort: small embedded seed
                rows = DEFAULT_SEED

        results: List[Tuple[str, str, float, float]] = []
        seen: Set[Tuple[str, str]] = set()

        if use_network:
            # For each district, try a few common keywords to surface reputable private preschools
            keywords = ["Montessori", "Anaokulu", "Preschool", "Kindergarten", "Kreş", "Özel Anaokulu"]
            per_district_quota = max(1, target_total // len(TARGET_DISTRICTS))
            for district in TARGET_DISTRICTS:
                collected = 0
                for kw in keywords:
                    if collected >= per_district_quota:
                        break
                    q = f"{kw}, {district}, Istanbul, Türkiye"
                    self.stdout.write(f"Query: {q}")
                    try:
                        places = geolocator.geocode(q, exactly_one=False, limit=10, timeout=10)
                    except Exception as exc:  # pragma: no cover
                        self.stderr.write(f"  Query failed: {exc}")
                        time.sleep(1)
                        continue
                    if not places:
                        time.sleep(1)
                        continue

                    for p in places:
                        name = (getattr(p, "raw", {}).get("display_name") or str(p)).split(",")[0].strip()
                        lat, lon = float(p.latitude), float(p.longitude)
                        key = (name, district)
                        if key in seen:
                            continue
                        seen.add(key)
                        results.append((name, district, lat, lon))
                        collected += 1
                        if len(results) >= target_total or collected >= per_district_quota:
                            break
                    time.sleep(1)  # Nominatim politeness
        else:
            # Use provided CSV or small seed
            for r in rows:
                results.append((r.name, r.district, r.lat, r.lon))

        created, updated = 0, 0
        to_create: List[Preschool] = []

        for i, (name, district, lat, lon) in enumerate(results, start=1):
            if dry:
                self.stdout.write(f"[{i}] {district}: {name} -> ({lat:.6f}, {lon:.6f})")
                continue

            if overwrite:
                obj, was_created = Preschool.objects.update_or_create(
                    name=name,
                    district=district,
                    defaults={"location": Point(lon, lat, srid=4326)},
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
            else:
                if not Preschool.objects.filter(name=name, district=district).exists():
                    to_create.append(Preschool(name=name, district=district, location=Point(lon, lat, srid=4326)))
                    created += 1

        if to_create:
            Preschool.objects.bulk_create(to_create, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}, Total prepared: {len(results)}"))

