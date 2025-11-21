Import Malls and Parks (CSV)

Command

- python manage.py import_malls_parks_csv --path <CSV_PATH_OR_URL> [--truncate] [--encoding latin-1] [--name-field ...] [--lat-field ...] [--lon-field ...] [--type-field type] [--kind mall|park]

Examples

1) Single CSV with a type column

```bash
python manage.py import_malls_parks_csv \
  --path /mnt/kalii/Real-Estate-Management-/mallsnparks.csv \
  --encoding latin-1 \
  --name-field name --lat-field lat --lon-field lon --type-field category \
  --truncate
```

2) CSV without a type column (import all as malls)

```bash
python manage.py import_malls_parks_csv \
  --path data/malls.csv --kind mall --name-field MallName --lat-field Latitude --lon-field Longitude --truncate
```

After import

- Enable layers and radii in Admin → Map Generation Config (enable_malls, enable_parks, radius_malls, radius_parks, max_malls, max_parks)
- Rebuild contexts:

```bash
python manage.py build_listing_context --limit 24 --source coralcity --combined
```

