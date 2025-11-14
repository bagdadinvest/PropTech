import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.gis.geos import GEOSGeometry

# Ensure you have installed the required library: pip install overpy
try:
    import overpy
except ImportError:
    class MockOverpassResult:
        nodes = []
    class MockOverpass:
        def query(self, q):
            print("--- WARNING: Overpass API simulation. Install 'overpy' for real data. ---")
            return MockOverpassResult()
    overpy = MockOverpass

# Assuming models are in stores_layer/models.py
from stores_layer.models import Grocery, Clothing

class Command(BaseCommand):
    help = 'Fetches store data using Overpass API and either loads it or dumps it for review.'

    def add_arguments(self, parser):
        parser.add_argument('config_file', type=str, help='Path to the JSON configuration file.')
        parser.add_argument(
            '--dump-file', 
            type=str, 
            help='If provided, saves the raw API result nodes to this file path (e.g., nodes.json) and skips database insertion.'
        )

    def _build_overpass_query(self, config):
        """Constructs the Overpass QL query string from the config tags and bbox."""
        search_criteria = config.get('search_criteria', {})
        bbox = search_criteria.get('bbox', [])

        if len(bbox) != 4:
            raise CommandError("BBox must contain 4 values: [min_lon, min_lat, max_lon, max_lat]")

        overpass_bbox = f"({bbox[1]}, {bbox[0]}, {bbox[3]}, {bbox[2]})"

        query_parts = ["[out:json];", "("]

        for tag_dict in search_criteria.get('tags', []):
            tag_selector = "node"
            
            for k, v in tag_dict.items():
                if k.endswith('~'):
                    tag_key = k.strip('~')
                    tag_selector += f'["{tag_key}"~"{v}"]'
                else:
                    tag_selector += f'["{k}"="{v}"]'
            
            query_parts.append(f'{tag_selector}{overpass_bbox};')
        
        query_parts.append(f");")
        query_parts.append("out center;")

        return "\n".join(query_parts)


    def handle(self, *args, **options):
        config_path = options['config_file']
        dump_file = options['dump_file']

        # 1. Load config
        if not os.path.exists(config_path):
            raise CommandError(f'Configuration file not found at: {config_path}')
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError:
            raise CommandError(f'Error decoding JSON from file: {config_path}')

        model_type = config.get('model_type')
        if model_type not in ['grocery', 'clothing']:
            raise CommandError(f"Invalid model_type in config: {model_type}. Must be 'grocery' or 'clothing'.")

        TargetModel = Grocery if model_type == 'grocery' else Clothing
        self.stdout.write(self.style.NOTICE(f"--- Starting Overpass load for {TargetModel.__name__} ---"))

        # 2. Construct and Fetch
        try:
            query = self._build_overpass_query(config)
            self.stdout.write(f"\nConstructed Query:\n---\n{query}\n---\n")
            
            api = overpy.Overpass() 
            result = api.query(query)
            self.stdout.write(f"Query executed. Found {len(result.nodes)} nodes.")
        except Exception as e:
            raise CommandError(f"Overpass API call failed: {e}")
        
        
        # 3. DUMP or LOAD
        if dump_file:
            # DUMP: Save to file and skip DB insertion (for review)
            self.stdout.write(self.style.NOTICE(f"Saving {len(result.nodes)} nodes to {dump_file} (skipping DB insertion)..."))
            
            dump_data = [{
                'osm_id': node.id,
                'name': node.tags.get('name', node.tags.get('brand', f"OSM ID: {node.id}")),
                'lat': float(node.lat),
                'lon': float(node.lon),
                'tags': node.tags,
            } for node in result.nodes]
            
            try:
                with open(dump_file, 'w', encoding='utf-8') as f:
                    json.dump(dump_data, f, indent=4)
                self.stdout.write(self.style.SUCCESS(f"Successfully dumped data to: {dump_file}"))
                return
            except Exception as e:
                raise CommandError(f"Failed to write dump file: {e}")
        
        # LOAD: Process and save data to DB (Only runs if dump_file is NOT set)
        creations_count = 0
        try:
            with transaction.atomic():
                for node in result.nodes:
                    store_name = node.tags.get('name', node.tags.get('brand', f"{TargetModel.__name__} (OSM ID: {node.id})"))
                    
                    try:
                        lat = float(node.lat)
                        lon = float(node.lon)
                        point_wkt = f'POINT ({lon} {lat})'
                        store_location = GEOSGeometry(point_wkt, srid=4326)
                        
                        TargetModel.objects.create(
                            name=store_name,
                            location=store_location
                        )
                        creations_count += 1
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"Skipping node {node.id} due to data error: {e}"))
                        continue
                
                self.stdout.write(self.style.SUCCESS(
                    f"\nSuccessfully loaded {creations_count} records for {TargetModel.__name__}."
                ))

        except Exception as e:
            raise CommandError(f"Database operation failed. Transaction rolled back: {e}")