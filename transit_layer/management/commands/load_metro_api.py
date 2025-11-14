# transit_layer/management/commands/load_metro_api.py

import requests
import sys
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point
from django.db import transaction

# Import the model you defined
from transit_layer.models import MetroStation 

# The IBB API endpoint
API_URL = "https://api.ibb.gov.tr/MetroIstanbul/api/MetroMobile/V2/GetStations"

class Command(BaseCommand):
    help = 'Loads Metro/Tram station data from the IBB API and saves it to MetroStation model.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--truncate',
            action='store_true',
            help='Deletes all existing MetroStation records before importing.',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting API data fetch for Metro Stations..."))

        if options['truncate']:
            self.stdout.write(self.style.WARNING("Truncating existing MetroStation data..."))
            MetroStation.objects.all().delete()
        
        try:
            response = requests.get(API_URL, timeout=10)
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            data = response.json()
        except requests.exceptions.RequestException as e:
            raise CommandError(f"API Request Failed: {e}")
        except ValueError:
            raise CommandError("API Response is not valid JSON.")
        
        station_data = data.get('Data', [])
        total_stations = len(station_data)
        self.stdout.write(self.style.SUCCESS(f"API Success. Found {total_stations} stations to process."))

        if not total_stations:
            self.stdout.write(self.style.NOTICE("No station data found in the API response. Exiting."))
            return

        # Use transaction.atomic for performance and data integrity
        with transaction.atomic():
            created_count = 0
            updated_count = 0
            
            for i, item in enumerate(station_data):
                # 1. Data Extraction
                try:
                    name = item['Description'].strip() if item.get('Description') else item['Name'].strip()
                    lat = float(item['DetailInfo']['Latitude'])
                    lon = float(item['DetailInfo']['Longitude'])
                except (KeyError, ValueError) as e:
                    self.stdout.write(self.style.ERROR(f"Skipping station {item.get('Name', 'Unknown')}: Missing or invalid field ({e})."))
                    continue

                # 2. GeoDjango Point Conversion (Lon, Lat order for PostGIS)
                point_location = Point(lon, lat, srid=4326)
                
                # 3. Upsert Logic (Update or Create)
                station, created = MetroStation.objects.update_or_create(
                    name=name,
                    defaults={
                        'location': point_location,
                        # Add other fields here as you expand the model (e.g., 'line_name': item['LineName'])
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

                # 4. Console Progress Indicator
                # The '\r' character returns the cursor to the start of the line
                progress = (i + 1) / total_stations
                sys.stdout.write(f"\rProgress: [{int(progress * 100):3d}%] | Processed: {i + 1}/{total_stations} | Created: {created_count} | Updated: {updated_count}",)
                sys.stdout.flush()

            self.stdout.write('\n' + self.style.SUCCESS(
                f"--- Load Complete. Total stations: {total_stations}. Created: {created_count}. Updated: {updated_count}. ---"
            ))
