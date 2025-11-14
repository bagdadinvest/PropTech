import csv
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from education_layer.models import InternationalSchool


@dataclass
class IntlSchoolRow:
    name: str
    address_text: str
    curriculum: str


def read_csv(path: Path) -> Optional[List[IntlSchoolRow]]:
    if not path.exists():
        return None
    rows: List[IntlSchoolRow] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            name = (r.get("name") or "").strip()
            address = (r.get("address_text") or r.get("address") or "").strip()
            curriculum = (r.get("curriculum") or "").strip()
            if name and address:
                rows.append(IntlSchoolRow(name=name, address_text=address, curriculum=curriculum))
    return rows or None


# A compact default seed to make the command usable offline.
# Provide <BASE_DIR>/data/international_schools.csv to override and supply ~30 entries.
DEFAULT_SEED: List[IntlSchoolRow] = [
    IntlSchoolRow(
        name="Istanbul International Community School (IICS)",
        address_text="Marmara Campus, Büyükçekmece, Istanbul",
        curriculum="IB",
    ),
    IntlSchoolRow(
        name="The British International School Istanbul (BISI)",
        address_text="Zekeriyaköy, Sarıyer, Istanbul",
        curriculum="British",
    ),
    IntlSchoolRow(
        name="MEF International School Istanbul",
        address_text="Ulus, Beşiktaş, Istanbul",
        curriculum="IB",
    ),
    IntlSchoolRow(
        name="Tarabya British Schools",
        address_text="Tarabya, Sarıyer, Istanbul",
        curriculum="British",
    ),
    IntlSchoolRow(
        name="İstanbul International School (IIS)",
        address_text="Beylikdüzü, Istanbul",
        curriculum="British",
    ),
]


class Command(BaseCommand):
    help = (
        "Load InternationalSchool records.\n"
        "- Reads <BASE_DIR>/data/international_schools.csv if present with columns: name,address_text,curriculum.\n"
        "- Otherwise uses a small embedded seed list (override recommended to reach ~30).\n"
        "- Geocodes each address via Nominatim and bulk creates/updates entries."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument("--dry-run", action="store_true", help="Print results without writing to DB")
        parser.add_argument("--overwrite", action="store_true", help="Overwrite existing entries by name")
        parser.add_argument(
            "--csv",
            type=str,
            default="",
            help="Path to CSV with columns name,address_text,curriculum",
        )

    def handle(self, *args, **options):
        dry = options.get("dry_run", False)
        overwrite = options.get("overwrite", False)
        csv_path = Path(options.get("csv") or "")

        data_dir = Path(settings.BASE_DIR) / "data"
        default_csv = data_dir / "international_schools.csv"

        rows = read_csv(csv_path) if csv_path else None
        if rows is None:
            rows = read_csv(default_csv)
        rows = rows or DEFAULT_SEED

        try:
            from geopy.geocoders import Nominatim  # type: ignore
        except Exception:  # pragma: no cover
            self.stderr.write("geopy is not installed. Install it first: pip install geopy")
            raise

        geolocator = Nominatim(user_agent="istanbul_proptech_edu_intl")

        created, updated, failed = 0, 0, 0
        to_create: List[InternationalSchool] = []

        for i, row in enumerate(rows, start=1):
            q = f"{row.address_text}, Istanbul, Türkiye"
            self.stdout.write(f"[{i}/{len(rows)}] Geocoding: {row.name} -> {q}")
            try:
                loc = geolocator.geocode(q, timeout=10)
            except Exception as exc:  # pragma: no cover
                self.stderr.write(f"  Geocoding failed: {exc}")
                failed += 1
                time.sleep(1)
                continue

            if not loc:
                self.stderr.write("  No result")
                failed += 1
                time.sleep(1)
                continue

            lon, lat = float(loc.longitude), float(loc.latitude)

            if dry:
                self.stdout.write(f"  -> ({lat:.6f}, {lon:.6f}) [{row.curriculum}]")
            else:
                if overwrite:
                    obj, was_created = InternationalSchool.objects.update_or_create(
                        name=row.name,
                        defaults={
                            "address_text": row.address_text,
                            "curriculum": row.curriculum,
                            "location": Point(lon, lat, srid=4326),
                        },
                    )
                    if was_created:
                        created += 1
                    else:
                        updated += 1
                else:
                    # Collect for bulk create if not exists; else skip
                    if not InternationalSchool.objects.filter(name=row.name).exists():
                        to_create.append(
                            InternationalSchool(
                                name=row.name,
                                address_text=row.address_text,
                                curriculum=row.curriculum,
                                location=Point(lon, lat, srid=4326),
                            )
                        )
                        created += 1
                    else:
                        updated += 0  # no-op

            # Nominatim: 1 req/sec politeness
            time.sleep(1)

        if not dry and to_create:
            InternationalSchool.objects.bulk_create(to_create, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}, Failed: {failed}"))

