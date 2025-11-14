# stores_layer/management/commands/load_stores.py

import json
import sys
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point
from django.db import transaction

# Import the models
from stores_layer.models import Clothing, Grocery


class Command(BaseCommand):
    help = 'Loads Clothing and Grocery store data from JSON files and saves them to the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--truncate',
            action='store_true',
            help='Deletes all existing Clothing and Grocery records before importing.',
        )
        parser.add_argument(
            '--store-type',
            type=str,
            choices=['clothing', 'grocery', 'all'],
            default='all',
            help='Specify which store type to load: "clothing", "grocery", or "all" (default).',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting store data import..."))

        if options['truncate']:
            self.stdout.write(self.style.WARNING("Truncating existing store data..."))
            if options['store_type'] in ['clothing', 'all']:
                Clothing.objects.all().delete()
            if options['store_type'] in ['grocery', 'all']:
                Grocery.objects.all().delete()

        # Get the base directory where the JSON files are located (project root)
        base_dir = Path(__file__).resolve().parent.parent.parent.parent

        store_types = []
        if options['store_type'] in ['clothing', 'all']:
            store_types.append(('clothing', Clothing, base_dir / 'clothing_nodes_to_review.json'))
        if options['store_type'] in ['grocery', 'all']:
            store_types.append(('grocery', Grocery, base_dir / 'grocery_nodes_to_review.json'))

        total_created = 0
        total_updated = 0

        for store_name, model_class, json_path in store_types:
            self.stdout.write(self.style.NOTICE(f"\nProcessing {store_name.upper()} stores..."))

            if not json_path.exists():
                raise CommandError(f"JSON file not found: {json_path}")

            try:
                with open(json_path, 'r', encoding='utf-8') as jsonfile:
                    data = json.load(jsonfile)
                    total_rows = len(data)

                    if not total_rows:
                        self.stdout.write(self.style.NOTICE(f"No data found in {json_path}. Skipping."))
                        continue

                    self.stdout.write(self.style.SUCCESS(f"Found {total_rows} {store_name} stores to process."))

                    # Use transaction.atomic for performance and data integrity
                    with transaction.atomic():
                        created_count = 0
                        updated_count = 0

                        for i, item in enumerate(data):
                            # 1. Data Extraction
                            try:
                                name = item['name'].strip() if item.get('name') else None
                                lat = float(item['lat'])
                                lon = float(item['lon'])

                                if not name:
                                    self.stdout.write(
                                        self.style.ERROR(
                                            f"Skipping item {item.get('osm_id', 'Unknown')}: Missing name."
                                        )
                                    )
                                    continue

                            except (KeyError, ValueError, TypeError) as e:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f"Skipping item {item.get('osm_id', 'Unknown')}: Missing or invalid field ({e})."
                                    )
                                )
                                continue

                            # 2. GeoDjango Point Conversion (Lon, Lat order for PostGIS)
                            point_location = Point(lon, lat, srid=4326)

                            # 3. Upsert Logic (Update or Create)
                            # Use name as the unique identifier
                            store, created = model_class.objects.update_or_create(
                                name=name,
                                defaults={
                                    'location': point_location,
                                }
                            )

                            if created:
                                created_count += 1
                            else:
                                updated_count += 1

                            # 4. Console Progress Indicator
                            progress = (i + 1) / total_rows
                            sys.stdout.write(
                                f"\rProgress: [{int(progress * 100):3d}%] | Processed: {i + 1}/{total_rows} | "
                                f"Created: {created_count} | Updated: {updated_count}"
                            )
                            sys.stdout.flush()

                        self.stdout.write(
                            '\n' + self.style.SUCCESS(
                                f"--- {store_name.capitalize()} Load Complete. Total: {total_rows}. "
                                f"Created: {created_count}. Updated: {updated_count}. ---"
                            )
                        )

                        total_created += created_count
                        total_updated += updated_count

            except json.JSONDecodeError as e:
                raise CommandError(f"Error decoding JSON from {json_path}: {e}")
            except Exception as e:
                raise CommandError(f"Error processing {store_name} data: {e}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n=== ALL STORES LOADED ===\nTotal Created: {total_created}\nTotal Updated: {total_updated}"
            )
        )
