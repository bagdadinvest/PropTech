# Data Import and Map Generation Guide

This guide shows how to load CSV/JSON data into the database and generate static HTML map files with inlined icons and computed distances.

## Prerequisites

- Working PostGIS connection configured in `IstanbulPropTech/settings.py`.
- Python virtualenv set up (repo includes `venv/`).
- Run migrations first:

```
venv/bin/python manage.py migrate
```

Optional: ensure feature toggles in `MapGenerationConfig` are on (they are by default from earlier steps). You can edit via Django admin or let commands auto-create defaults.

## Importing Data from CSV/JSON

Import commands accept either local file paths or HTTP(S) URLs. Longitude/latitude are expected in WGS84 (EPSG:4326).

### Metro stations (CSV or GeoJSON)

```
venv/bin/python manage.py load_rail_data --file data/metro_stations.csv --truncate
# Auto-detects name and lon/lat columns; supports GeoJSON as well
```

### Metrobus stations (CSV)

```
venv/bin/python manage.py import_metrobus_csv --path data/metrobus.csv --truncate \
  --name-field name --lat-field lat --lon-field lon
```

### Bus stops (CSV)

```
venv/bin/python manage.py import_bus_stops_csv --path data/bus_stops.csv --truncate \
  --name-field stop_name --lat-field stop_lat --lon-field stop_lon
```

### Taxi stands (CSV or JSON)

CSV:
```
venv/bin/python manage.py import_taxi_csv --path data/taxi_stands.csv --truncate \
  --name-field name --lat-field lat --lon-field lon
```

JSON (array of objects with name, lat, lon):
```
venv/bin/python manage.py import_taxi_json --path data/taxi_stands.json --truncate
```

### Malls and Parks (CSV)

The CSV should contain columns for `name`, `lat`, `lon`, and either a `type` column (values like `mall`/`park`) or pass a fixed kind.

```
venv/bin/python manage.py import_malls_parks_csv --path data/parks_malls.csv --truncate \
  --name-field name --lat-field lat --lon-field lon --type-field type

# Or import a CSV as all malls (no type column needed):
venv/bin/python manage.py import_malls_parks_csv --path data/malls.csv --kind mall --truncate \
  --name-field name --lat-field lat --lon-field lon
```

### Grocery and Clothing stores

Option A (JSON, recommended): place JSON files at the repo root named:
- `grocery_nodes_to_review.json`
- `clothing_nodes_to_review.json`

Each JSON file should be an array of objects with at minimum: `name`, `lat`, `lon`.

Then run:
```
venv/bin/python manage.py load_stores --truncate --store-type grocery
venv/bin/python manage.py load_stores --truncate --store-type clothing
```

Option B (CSV via a quick shell snippet): if you only have CSV (columns: `name,lat,lon`), you can import with a one-liner in the Django shell.

```
venv/bin/python manage.py shell -c "\
import csv; from django.contrib.gis.geos import Point; \
from stores_layer.models import Grocery; \
Grocery.objects.all().delete(); \
rows=csv.DictReader(open('data/grocery.csv')); \
[Grocery.objects.create(name=r['name'].strip() or 'Store', location=Point(float(r['lon']), float(r['lat']), srid=4326)) for r in rows if r.get('lat') and r.get('lon')]\
"
```

Repeat for `Clothing` by replacing the model.

## Syncing/Seeding Listings (points to build maps around)

Maps are generated around listing locations stored in `ExternalListing`. You can either sync from an API or seed manually.

Sync from API returning items with `id, title, price, lat, lng`:
```
venv/bin/python manage.py sync_external_listings --api-url https://example/api/listings --limit 24 --source coralcity
```

Or create a few by hand in Django admin under External Listings.

## Compute nearest distances (optional but recommended)

This persists nearest distances per listing to the DB for use on your website.

```
BICYCLE_GEOJSON_PATH="Istanbul Bicycle Paths Data" \
venv/bin/python manage.py update_nearest_distances --source coralcity --all
```

## Generate static map files

This creates one HTML map per `ExternalListing` in `distill_out/simplified/maps` with:
- Inlined icons (base64)
- Aspect preserving icons (with forced 24×24 for taxi/metrobus/grocery)
- Inlined nearby layers (metro, metrobus, bus, grocery, clothing, malls, parks, taxi, minibus lines, bicycle paths)
- Popups with distances in meters

```
BICYCLE_GEOJSON_PATH="Istanbul Bicycle Paths Data" \
venv/bin/python manage.py generate_listing_maps --limit 24 --preserve-icon-aspect
```

Notes:
- Set `--limit` to control how many maps to generate.
- To export for sharing:
```
cd distill_out/simplified
zip -r maps_export.zip maps/*.html
```

## Troubleshooting

- Unicode/encoding issues when importing CSV: try `--encoding latin-1`.
- Missing columns: all import commands accept `--name-field`, `--lat-field`, `--lon-field` to match your CSV headers.
- No bicycle/minibus data: the generator reads local files. Ensure these exist:
  - Bicycle: set env `BICYCLE_GEOJSON_PATH="Istanbul Bicycle Paths Data"` or provide `data/bicycle_roads.geojson`.
  - Minibus: place `Minibus Lines Data` or `data/minibus_lines.geojson` at repo root.
- Layer toggles/radii: edit via Django Admin → Map Generation Config, or rely on defaults.

