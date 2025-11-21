Overview

- Goal: generate static, per-listing answers (nearest transit and amenities within walking distance) and ship them as JSON used by a standalone map. No always-on Django needed for this part.
- Inputs: listing points (GeoJSON from your website API export or a snapshot).
- Process: for each listing, query Istanbul open-data APIs within a radius; compute distances; keep the few closest; write a single simplified GeoJSON consumed by the frontend.
- Output: `distill_out/simplified/api/listings-simplified.geojson` matching the current map expectations.

Why this approach works well

- Less data to move: only fetch around listings, not the whole city.
- Static hosting: output is a flat file; the map reads it via `fetch()`.
- Fresh but controlled: add a TTL or rebuild cadence to refresh data without a server running 24/7.
- Low coupling: can plug different providers or datasets per POI type.

What’s included here

- `tools/nearby_enrichment/enrich_listings.py`: CLI to enrich listings and write the simplified GeoJSON.
- `tools/nearby_enrichment/providers.py`: provider functions with local fallbacks; plug Istanbul APIs here.
- `tools/nearby_enrichment/spatial.py`: small helpers for distance calculations.

Usage

1) Prepare input listings
- Default path assumed by the CLI: `distill_out/simplified/api/listings.geojson` (Point features with `properties.id`, `title`, `price`, `size_sqm`, optional `image_url`/`images`).

2) Run enrichment

```bash
python -m tools.nearby_enrichment.enrich_listings \
  --input distill_out/simplified/api/listings.geojson \
  --output distill_out/simplified/api/listings-simplified.geojson \
  --radius-m 1200 \
  --stations 3 --grocery 3 --clothing 3
```

3) Open the simplified map
- `distill_out/simplified/index.html` already fetches `/api/listings-simplified.geojson` and renders markers and stats.

Provider integration notes

- Metro/metrobus/minibus: Prefer endpoints supporting spatial filters (buffer/nearest). Many WFS/GeoServer stacks accept `CQL_FILTER=DWITHIN(geom,POINT(lon lat),RADIUS,meters)` or a `bbox` query. ArcGIS REST variants use `geometry` + `spatialRel=esriSpatialRelIntersects`.
- Amenities (grocery, clothing, schools, hospitals): Either municipal open-data layers or curated vendor lists. Normalize to `{ id, name, location(Point), distance_m }`.
- Rate limiting: add simple caching by rounded grid key (e.g., 250 m), so nearby listings reuse the same provider response.
- TTL: cache files under `data/cache/<provider>/<key>.json`; expire on a schedule or during rebuilds.

Output schema (per listing)

- `properties.closest_stations`: list of `{ id, name, distance_m, location(Point) }`
- `properties.closest_grocery_stores`: same shape
- `properties.closest_clothing_stores`: same shape
- Core fields are passed through: `id`, `title`, `price`, `size_sqm`, `image_url`, `images`
- File-level `config`: counts for quick diagnostics in the UI

Future enhancements (optional)

- Walking time: replace straight-line distance with walking time using OSRM/OpenRouteService when available.
- Isochrone-based filter: filter POIs within 10–15 minute walk polygons instead of a fixed radius.
- More POI types: schools, hospitals, parks; each as a provider module.
- Incremental rebuilds: only recompute for changed or new listings.

Caveats

- API terms and quotas: verify municipal API limits and add backoff/retry where needed.
- Availability: add local fallbacks for demo/CI; production should use live endpoints with caching.

