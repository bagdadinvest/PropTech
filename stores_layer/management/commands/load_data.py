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
            # Simulation response for local testing if overpy is not installed
            print("--- WARNING: Overpass API simulation. Install 'overpy' for real data. ---")
            return MockOverpassResult()
    overpy = MockOverpass

from stores_layer.models import Grocery, Clothing

class Command(BaseCommand):
    help = 'Loads store data using criteria defined in a JSON configuration file via Overpass API.'

    def add_arguments(self, parser):
        parser.add_argument('config_file', type=str, help='Path to the JSON configuration file.')

    def _build_overpass_query(self, config):
        """
        Constructs the Overpass QL query string from the config tags and bbox.
        FIXED: Ensures tags are correctly concatenated without repeating the 'node' element.
        """
        search_criteria = config.get('search_criteria', {})
        bbox = search_criteria.get('bbox', [])

        if len(bbox) != 4:
            raise CommandError("BBox must contain 4 values: [min_lon, min_lat, max_lon, max_lat]")

        # Overpass bbox format is (south_lat, west_lon, north_lat, east_lon)
        # Bbox from config: [min_lon, min_lat, max_lon, max_lat] -> [bbox[1], bbox[0], bbox[3], bbox[2]]
        overpass_bbox = f"({bbox[1]}, {bbox[0]}, {bbox[3]}, {bbox[2]})"

        # Start of the query: Set timeout and output format
        query_parts = [
            "[out:json];",
            "(",
        ]

        # Add all tag rules
        for tag_dict in search_criteria.get('tags', []):
            tag_selector = "node" # Start the selector with the element type (node, way, or relation)
            
            # Build the selector string (e.g., node["shop"="supermarket"]["name"~"Migros"])
            for k, v in tag_dict.items():
                if k.endswith('~'):
                    # Regex match (e.g., name~: "Migros|A101")
                    tag_key = k.strip('~')
                    tag_selector += f'["{tag_key}"~"{v}"]'
                else:
                    # Exact match (e.g., shop: "supermarket")
                    tag_selector += f'["{k}"="{v}"]'
            
            # Append the full selector with bounding box and semicolon
            query_parts.append(f'{tag_selector}{overpass_bbox};')
        
        query_parts.append(f");")
        query_parts.append("out center;")

        return "\n".join(query_parts)


    def handle(self, *args, **options):
        config_path = options['config_file']

        # 1. Load and validate the configuration file
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

        # 2. Determine the target model
        TargetModel = Grocery if model_type == 'grocery' else Clothing
        
        self.stdout.write(self.style.NOTICE(f"--- Starting Overpass load for {TargetModel.__name__} ---"))

        # 3. Construct the Overpass QL query
        try:
            query = self._build_overpass_query(config)
            self.stdout.write(f"\nConstructed Query:\n---\n{query}\n---\n") # Show the query for debugging
        except CommandError as e:
            raise e
        except Exception as e:
            raise CommandError(f"Error building Overpass query: {e}")

        # 4. Fetch data from Overpass API
        try:
            # Overpass API initialization
            api = overpy.Overpass() 
            result = api.query(query)
            self.stdout.write(f"Query executed. Found {len(result.nodes)} nodes.")
        except Exception as e:
            # Re-raise with clearer context if the API fails
            raise CommandError(f"Overpass API call failed. Check connectivity, query syntax, or Overpass service status: {e}")
        
        # 5. Process and Save Data using atomic transaction
        creations_count = 0
        
        try:
            with transaction.atomic():
                for node in result.nodes:
                    # Use a descriptive name, prioritizing 'name' tag
                    store_name = node.tags.get('name', node.tags.get('brand', f"{TargetModel.__name__} (OSM ID: {node.id})"))
                    
                    try:
                        lat = float(node.lat)
                        lon = float(node.lon)
                        
                        # CRITICAL: Lon/Lat order for GEOSGeometry POINT (longitude latitude)
                        point_wkt = f'POINT ({lon} {lat})'
                        store_location = GEOSGeometry(point_wkt, srid=4326)
                        
                        TargetModel.objects.create(
                            name=store_name,
                            location=store_location
                        )
                        creations_count += 1

                    except (ValueError, KeyError) as e:
                        self.stderr.write(self.style.ERROR(f"Skipping node {node.id} due to missing coordinates or tag error: {e}"))
                        continue
                
                # 6. Report results
                self.stdout.write(self.style.SUCCESS(
                    f"\nSuccessfully loaded {creations_count} records for {TargetModel.__name__}."
                ))

        except Exception as e:
            # Rollback on any database error
            raise CommandError(f"Database operation failed. Transaction rolled back: {e}")