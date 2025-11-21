Import Metrobus Stations (CSV)

Command

- python manage.py import_metrobus_csv --path <CSV_PATH_OR_URL> [--truncate] [--encoding latin-1] [--name-field DurakAdi] [--lat-field lat] [--lon-field lon]

Examples

1) Local file

```bash
python manage.py import_metrobus_csv --path data/metrobus_stations.csv --truncate --encoding latin-1 --name-field DurakAdi --lat-field Enlem --lon-field Boylam
```

2) Remote CSV

```bash
python manage.py import_metrobus_csv --path 'https://example.com/metrobus.csv' --truncate
```

Notes

- The command writes into transit_layer.MetrobusStation, which is already used by the build_listing_context command for nearest lookups.
- Use --encoding latin-1 if Turkish characters appear garbled.
- If your CSV has different column names, pass them via the --*-field options.

