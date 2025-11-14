Place input files here for data loading commands.

Expected files:
- Rail (Metro/Tram): 2022-yili-rayli-ulasim-istasyonlar-vektor-verisi.csv or a GeoJSON equivalent.
  The command will auto-detect a file matching '*rayli*istasyon*.(csv|geojson)'.

- Metrobus stations: metrobus_stations.txt (one station name per line). Optional.
  If absent, the loader uses an embedded list; verify it against Wikipedia's 44-stop list.

