Purpose

- Generate minimal, presentation-free JSON for each listing: name, point, and distances to nearby layers. The customer-facing app handles all styling and popups.

Command

- python manage.py build_listing_context [--listing-id EXT_ID | --all | --limit N] [--source coralcity] [--out-dir distill_out/simplified/contexts] [--combined]

Examples

1) One listing by external id

```bash
python manage.py build_listing_context --listing-id 25 --source coralcity
```

2) Latest 24 listings

```bash
python manage.py build_listing_context --limit 24 --source coralcity
```

3) All listings and a combined file

```bash
python manage.py build_listing_context --all --combined --source coralcity
```

Output

- Per listing: distill_out/simplified/contexts/listing_<external_id>_context.json
- Optional aggregate: distill_out/simplified/contexts/contexts.json when using --combined

Shape (example)

```json
{
  "listing": {"id": "25", "title": "...", "lat": 41.02, "lng": 28.67},
  "metro": [ {"id": 203, "name": "Atatürk Mahallesi", "distance_m": 1114.2, "location": {"type": "Point", "coordinates": [28.79, 41.05]} } ],
  "metrobus": [ ... ],
  "bus": [ ... ],
  "grocery": [ ... ],
  "clothing": [ ... ]
}
```

Configuration

- Edit in Admin: Map Generation Config
  - Toggle layers on/off
  - Set per-layer radius (meters) and max count

Data sources

- This command queries your DB tables (PostGIS) for distances:
  - transit_layer: MetroStation, MetrobusStation, BusStop
  - stores_layer: Grocery, Clothing
  - Pharmacy: add later when a model/provider exists

Notes

- External listings are expected in listings.ExternalListing (use sync_external_listings first).
- Outputs contain only the facts needed by the other app (no images, no styling).

