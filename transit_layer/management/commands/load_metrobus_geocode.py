import os
import time
from pathlib import Path
from typing import Iterable, List, Optional

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point

from transit_layer.models import MetrobusStation


def read_station_names_from_file(path: Path) -> Optional[List[str]]:
    if not path.exists():
        return None
    names: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            if name and not name.startswith("#"):
                names.append(name)
    return names or None


DEFAULT_STATION_NAMES: List[str] = [
    # TODO: Replace or verify against the official Wikipedia list of 44 Metrobus stops.
    # You can also create <BASE_DIR>/data/metrobus_stations.txt (one name per line)
    # to override this list without editing code.
    # The command will use that file if present.
    "Söğütlüçeşme",
    "Fikirtepe",
    "Uzunçayır",
    "Acıbadem",
    "Altunizade",
    "Burhaniye Mahallesi",
    "15 Temmuz Şehitler Köprüsü",
    "Zincirlikuyu",
    "Mecidiyeköy",
    "Çağlayan",
    "Okmeydanı",
    "Darülaceze - Perpa",
    "Halıcıoğlu",
    "Ayvansaray - Eyüp Sultan",
    "Edirnekapı",
    "Bayrampaşa - Maltepe",
    "Cevizlibağ",
    "Merter",
    "Zeytinburnu",
    "İncirli",
    "Bahçelievler",
    "Şirinevler - Ataköy",
    "Yenibosna",
    "Sefaköy",
    "Beşyol",
    "Florya",
    "Cennet Mahallesi",
    "Küçükçekmece",
    "Başakşehir - Şehir Hastanesi",
    "Halkalı",
    "Altınşehir",
    "İETT Garajı",
    "Avcılar",
    "Şükrübey",
    "Beylikdüzü Belediye",
    "Beylikdüzü",
    "Güzelyurt",
    "Haramidere",
    "Haramidere Sanayi",
    "Saadetdere Mahallesi",
    "İnönü Mahallesi",
    "Hadımköy",
    "Cumhuriyet Mahallesi",
    "Büyükşehir Belediyesi Sosyal Tesisleri",
    "TUYAP",
]


class Command(BaseCommand):
    help = (
        "Geocode 44 Metrobus station names and load into MetrobusStation.\n"
        "- Reads names from <BASE_DIR>/data/metrobus_stations.txt if present (one per line).\n"
        "- Otherwise uses the embedded list (verify to ensure the full official set).\n"
        "- Uses Nominatim via geopy and respects 1 req/sec politeness."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only print geocoded results; do not write to DB",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite coordinates for existing station names",
        )

    def handle(self, *args, **options):
        dry = options.get("dry_run", False)
        overwrite = options.get("overwrite", False)

        # Build station list
        data_dir = Path(settings.BASE_DIR) / "data"
        names_file = data_dir / "metrobus_stations.txt"
        station_names = read_station_names_from_file(names_file) or DEFAULT_STATION_NAMES

        try:
            from geopy.geocoders import Nominatim  # type: ignore
        except Exception as exc:  # pragma: no cover
            self.stderr.write(
                "geopy is not installed. Install it first, e.g., pip install geopy"
            )
            raise

        geolocator = Nominatim(user_agent="istanbul_proptech_metrobus_loader")

        created = 0
        updated = 0
        for i, name in enumerate(station_names, start=1):
            query = f"{name}, Istanbul, Türkiye"
            self.stdout.write(f"[{i}/{len(station_names)}] Geocoding: {query}")
            try:
                loc = geolocator.geocode(query, timeout=10)
            except Exception as exc:  # pragma: no cover
                self.stderr.write(f"  Geocoding failed: {exc}")
                time.sleep(1)
                continue

            if not loc:
                self.stderr.write("  No result")
                time.sleep(1)
                continue

            lon, lat = float(loc.longitude), float(loc.latitude)
            if dry:
                self.stdout.write(f"  -> ({lat:.6f}, {lon:.6f})")
            else:
                if overwrite:
                    obj, was_created = MetrobusStation.objects.update_or_create(
                        name=name, defaults={"location": Point(lon, lat, srid=4326)}
                    )
                else:
                    obj, was_created = MetrobusStation.objects.get_or_create(
                        name=name, defaults={"location": Point(lon, lat, srid=4326)}
                    )
                    if not was_created and overwrite:
                        obj.location = Point(lon, lat, srid=4326)
                        obj.save(update_fields=["location"]) 
                if was_created:
                    created += 1
                else:
                    updated += 1

            # Nominatim usage policy: at most 1 req/sec
            time.sleep(1)

        self.stdout.write(self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}"))

