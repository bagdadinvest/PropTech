Import Bus Stops (IMM CSV)

Why CSV

- Stable, no rate limits or auth, reproducible. Import once, then use local PostGIS for fast nearest lookups.

Command

- python manage.py import_bus_stops_csv --path <CSV_PATH_OR_URL> [--truncate] [--limit N]

Common usage

1) From remote URL (IMM Data Portal)

```bash
python manage.py import_bus_stops_csv \
  --path 'https://data.ibb.gov.tr/dataset/.../download/bus_stops.csv' \
  --truncate
```

2) From local file (already downloaded)

```bash
python manage.py import_bus_stops_csv --path data/imm_bus_stops.csv --truncate
```

Options

- --truncate: clear existing BusStop rows before import (recommended if replacing dataset)
- --limit: limit rows for testing
- --name-field/--lat-field/--lon-field: override column names if they differ (defaults: stop_name, stop_lat, stop_lon)

After import

- Build per-listing contexts to include bus stops (assuming Bus layer is enabled in Map Generation Config):

```bash
python manage.py build_listing_context --limit 24 --source coralcity --combined
```

