Purpose

- Pull listing pinpoints from your other Django app’s API and write a compact GeoJSON your map can use as targets (24 locations by default).

CLI

- Module: tools/nearby_enrichment/fetch_listings.py
- Help: python -m tools.nearby_enrichment.fetch_listings --help

Examples

1) Token-auth, common nested fields

```bash
python -m tools.nearby_enrichment.fetch_listings \
  --api-url https://example.com/api/listings/ \
  --auth "Token YOUR_API_TOKEN" \
  --param status=active --param city=Istanbul \
  --limit 24 --sort-by created_at \
  --lon-field location.longitude \
  --lat-field location.latitude \
  --id-field id \
  --title-field title \
  --price-field price \
  --size-field size_sqm \
  --image-url-field main_image \
  --images-field images \
  --output distill_out/simplified/api/listings.geojson
```

2) Bearer-auth, flat fields

```bash
python -m tools.nearby_enrichment.fetch_listings \
  --api-url https://example.com/api/listings/ \
  --auth "Bearer XYZ" \
  --limit 24 --sort-by updated_at --sort-asc \
  --lon-field longitude --lat-field latitude \
  --title-field title --price-field price
```

Response shapes supported

- A JSON list: [ { ... }, ... ]
- Or an object with results: { "results": [ { ... }, ... ], ... }

Output

- Writes GeoJSON to distill_out/simplified/api/listings.geojson with Point features and properties: id, title, price, size_sqm, image_url, images (when provided).
- This file is the sole input for the enrichment step, ensuring subsequent API calls target just these locations.

Next

- After fetching listings, run the enrichment pipeline to compute nearby transit/amenities and write listings-simplified.geojson.
```
python -m tools.nearby_enrichment.enrich_listings \
  --input distill_out/simplified/api/listings.geojson \
  --output distill_out/simplified/api/listings-simplified.geojson \
  --radius-m 1200 --stations 3 --grocery 3 --clothing 3
```

