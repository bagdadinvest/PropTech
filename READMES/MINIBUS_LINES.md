Minibus Lines (Polyline extraction per listing)

Goal

- Show only the segments of minibus routes that lie within a configurable radius around each listing, without importing the full dataset into the DB.

Input

- Root file: Minibus Lines Data (GeoJSON FeatureCollection)
- Feature geometry: LineString/MultiLineString
- Properties: HATNO (line id), HAT_ADI (name), GUZERGAH (description)

Configuration

- Admin → Map Generation Config
  - enable_minibus: toggle layer
  - radius_minibus: meters (e.g., 2500)
  - max_minibus: max lines to include

Build contexts

```bash
python manage.py build_listing_context --limit 24 --source coralcity --combined
```

Output shape

- Each per-listing JSON (listing_<id>_context.json) contains:
  - "minibus": [ { "id": HATNO, "name": HAT_ADI, "geometry": <GeoJSON geometry clipped to buffer> }, ... ]

Notes

- Buffering uses Web Mercator (EPSG:3857) for meter-accurate clipping, then transforms back to WGS84 (EPSG:4326).
- If transform/clipping fails, the full line geometry is included as a fallback.
- Environment override for file path: set MINIBUS_GEOJSON_PATH to a custom location.

