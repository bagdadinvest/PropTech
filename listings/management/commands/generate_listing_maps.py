from __future__ import annotations

import json
import base64
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.core.management.base import BaseCommand, CommandParser

from listings.models import ExternalListing, MapGenerationConfig
from tools.nearby_enrichment import db_providers as dbp
from tools.nearby_enrichment.minibus import nearby_minibus_segments, nearest_minibus_distance_m
from tools.nearby_enrichment.bicycle import nearby_bicycle_segments, nearest_bicycle_distance_m


HTML_SKELETON = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>Listing Map #{listing_id}</title>
  <link rel=\"stylesheet\" href=\"https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css\" />
  <style>
    html,body,#map{{height:100%;margin:0}} .badge{{position:absolute;top:8px;left:8px;background:#fff;padding:6px 10px;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,.15);z-index:1000;font:14px/1.4 system-ui}}
    /* Preserve logo aspect ratio when enabled */
    .ipt-icon{{max-width:{icon_max}px;max-height:{icon_max}px;width:auto !important;height:auto !important}}
    .ipt-icon.listing{{max-width:{listing_max}px;max-height:{listing_max}px}}
    /* Per-layer size overrides */
    .ipt-icon.metrobus{{max-width:{metrobus_max}px;max-height:{metrobus_max}px}}
    .ipt-icon.taxi{{max-width:{taxi_max}px;max-height:{taxi_max}px}}
    .ipt-icon.grocery{{max-width:{grocery_max}px;max-height:{grocery_max}px}}
  </style>
</head>
<body>
  <div id=\"map\"></div>
  <div class=\"badge\">{title} • {price}</div>
  <script src=\"https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js\"></script>
  <script>
    const DATA = {data_json};
    const ICONS = {icons_json};
    const PRESERVE_ASPECT = {preserve_aspect};
    // Force exact sizes for selected layers regardless of aspect mode
    const FIXED_SIZES = {{ metrobus: [24, 24], taxi: [24, 24], grocery: [24, 24] }};
    const map = L.map('map').setView([DATA.listing.lat, DATA.listing.lng], 15);
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ maxZoom:19, attribution:'© OpenStreetMap' }}).addTo(map);
    function makeDot(color, size) {{
      return L.divIcon({{html:`<div style=\\"width:${{size}}px;height:${{size}}px;border-radius:50%;background:${{color}};border:2px solid white\\"></div>`, iconSize:[size+4,size+4], iconAnchor:[(size+4)/2,(size+4)/2]}});
    }}
    function makeIconFrom(key, fallbackColor, size) {{
      const uri = ICONS[key];
      if (uri) {{
        if (FIXED_SIZES[key]) {{
          const sz = FIXED_SIZES[key];
          return L.icon({{iconUrl: uri, iconSize: sz, iconAnchor:[sz[0]/2, sz[1]/2]}});
        }}
        if (PRESERVE_ASPECT) return L.icon({{iconUrl: uri, className: 'ipt-icon ' + key}});
        return L.icon({{iconUrl: uri, iconSize:[size,size], iconAnchor:[size/2,size/2]}});
      }}
      return makeDot(fallbackColor, Math.max(12, size-4));
    }}
    const listingIcon = makeIconFrom('listing', '#667eea', 22);
    L.marker([DATA.listing.lat, DATA.listing.lng], {{icon: listingIcon}}).addTo(map).bindPopup(DATA.listing.title || ('Listing #' + DATA.listing.id));

    const metroIcon = ICONS['metro'] ? L.icon({{iconUrl: ICONS['metro'], iconSize:[24,24], iconAnchor:[12,12]}}) : L.icon({{iconUrl:'https://upload.wikimedia.org/wikipedia/commons/4/4f/Istanbul_Metro_Logo.svg', iconSize:[24,24], iconAnchor:[12,12]}});
    const metrobusIcon = makeIconFrom('metrobus', '#ff5722', 20);
    const busIcon = makeIconFrom('bus', '#2196f3', 18);
    const groceryIcon = makeIconFrom('grocery', '#4caf50', 18);
    const clothingIcon = makeIconFrom('clothing', '#9c27b0', 18);
    const taxiIcon = makeIconFrom('taxi', '#ffeb3b', 18);
    const mallIcon = makeIconFrom('malls', '#795548', 20);
    const parkIcon = makeIconFrom('parks', '#2e7d32', 20);

    (DATA.closest_stations||[]).forEach(s => {{
      L.marker([s.location.coordinates[1], s.location.coordinates[0]], {{icon: metroIcon}}).addTo(map).bindPopup(`${{s.name}} · ${{Math.round(s.distance_m)}} m`);
    }});
    (DATA.closest_metrobus||[]).forEach(s => {{
      L.marker([s.location.coordinates[1], s.location.coordinates[0]], {{icon: metrobusIcon}}).addTo(map).bindPopup(`${{s.name}} · ${{Math.round(s.distance_m)}} m`);
    }});
    (DATA.closest_bus_stops||[]).forEach(s => {{
      L.marker([s.location.coordinates[1], s.location.coordinates[0]], {{icon: busIcon}}).addTo(map).bindPopup(`${{s.name}} · ${{Math.round(s.distance_m)}} m`);
    }});
    (DATA.closest_grocery_stores||[]).forEach(s => {{
      L.marker([s.location.coordinates[1], s.location.coordinates[0]], {{icon: groceryIcon}}).addTo(map).bindPopup(`${{s.name}} · ${{Math.round(s.distance_m)}} m`);
    }});
    (DATA.closest_clothing_stores||[]).forEach(s => {{
      L.marker([s.location.coordinates[1], s.location.coordinates[0]], {{icon: clothingIcon}}).addTo(map).bindPopup(`${{s.name}} · ${{Math.round(s.distance_m)}} m`);
    }});
    (DATA.malls||[]).forEach(s => {{
      L.marker([s.location.coordinates[1], s.location.coordinates[0]], {{icon: mallIcon}}).addTo(map).bindPopup(`${{s.name}}`);
    }});
    (DATA.parks||[]).forEach(s => {{
      L.marker([s.location.coordinates[1], s.location.coordinates[0]], {{icon: parkIcon}}).addTo(map).bindPopup(`${{s.name}}`);
    }});
    // Minibus polylines (blue) for quick validation
    const minibusStyle = {{ color: '#1976d2', weight: 3, opacity: 0.8 }};
    (DATA.minibus||[]).forEach(line => {{
      try {{
        const g = L.geoJSON(line.geometry, {{ style: minibusStyle }}).addTo(map);
        if (line.name) g.bindPopup(line.name);
      }} catch (e) {{}}
    }});
    // Bicycle polylines (green)
    const bicycleStyle = {{ color: '#2e7d32', weight: 3, opacity: 0.8 }};
    (DATA.bicycle||[]).forEach(line => {{
      try {{
        const g = L.geoJSON(line.geometry, {{ style: bicycleStyle }}).addTo(map);
        if (line.name) g.bindPopup(line.name);
      }} catch (e) {{}}
    }});
    // Taxi markers
    (DATA.taxi||[]).forEach(s => {{
      L.marker([s.location.coordinates[1], s.location.coordinates[0]], {{icon: taxiIcon}}).addTo(map).bindPopup(`${{s.name}} · ${{Math.round(s.distance_m)}} m`);
    }});
  </script>
</body>
</html>
"""


class Command(BaseCommand):
    help = "Generate one static HTML Leaflet map per ExternalListing with inline nearby metro stations."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--source", default="coralcity", help="External source key to include")
        parser.add_argument("--listing-id", help="Generate only for this external listing id")
        parser.add_argument("--limit", type=int, default=24, help="Max listings to generate maps for")
        parser.add_argument("--radius-m", type=int, default=2000, help="Search radius for metro stations (meters)")
        parser.add_argument("--out-dir", default="distill_out/simplified/maps", help="Directory to write maps into")
        parser.add_argument("--preserve-icon-aspect", action="store_true", help="Render icons at natural aspect ratio with CSS max size")

    def handle(self, *args, **opts):
        out_dir = Path(opts["out_dir"]) ; out_dir.mkdir(parents=True, exist_ok=True)
        if opts.get("listing_id"):
            qs = ExternalListing.objects.filter(source=opts["source"], external_id=str(opts["listing_id"]))
        else:
            qs = ExternalListing.objects.filter(source=opts["source"]).order_by("-fetched_at")[: opts["limit"]]
        cfg = MapGenerationConfig.get_config()

        # Prepare inlined icons from distill_out/static/store_icons
        icons_dir = Path('distill_out/static/store_icons')

        def _read_b64(path: Path) -> Optional[str]:
            if not path.exists():
                return None
            data = path.read_bytes()
            ext = path.suffix.lower()
            mime = 'image/png'
            if ext == '.webp':
                mime = 'image/webp'
            elif ext == '.svg':
                mime = 'image/svg+xml'
            elif ext == '.ico':
                mime = 'image/x-icon'
            b64 = base64.b64encode(data).decode('ascii')
            return f"data:{mime};base64,{b64}"

        def _first_existing(names: List[str]) -> Optional[str]:
            for n in names:
                uri = _read_b64(icons_dir / n)
                if uri:
                    return uri
            return None

        icons: Dict[str, Optional[str]] = {
            # transit
            'metro': _first_existing(['metro.png', 'Metro.png', 'metro.ico', 'Metro.ico']),
            'metrobus': _first_existing(['Metrobus.png', 'metrobus.png', 'Metrobus.ico', 'metrobus.ico']),
            'bus': _first_existing(['IETT.png', 'bus.png', 'IETT.ico', 'bus.ico']),
            'taxi': _first_existing(['taxi.png', 'taxi.ico']),
            # amenities
            'grocery': _first_existing(['grocery.png', 'grocery.ico', 'bim.png', 'bim.ico', 'migros.png', 'migros.ico', 'a101.png', 'a101.ico', 'sok.png', 'sok.ico']),
            'clothing': _first_existing(['clothing.png', 'clothing.ico', 'mavi.png', 'mavi.ico']),
            'malls': _first_existing(['mall.png', 'mall.ico', 'malls.png', 'malls.ico']),
            'parks': _first_existing(['park.png', 'park.webp', 'parks.png', 'park.ico', 'parks.ico']),
            # extras
            'minibus': _first_existing(['minibus.png', 'minibus.ico', 'van.png', 'van.ico']),
            'bicycle': _first_existing(['bicycle.png', 'bicycle.ico']),
            'listing': _first_existing(['listing.png', 'listing.ico']),
        }

        written = 0
        for ext in qs:
            # Build nearby layers per config
            stations = dbp.nearby_metro_stations(lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_metro, limit=cfg.max_metro) if cfg.enable_metro else []
            metrobus = dbp.nearby_metrobus_stations(lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_metrobus, limit=cfg.max_metrobus) if cfg.enable_metrobus else []
            bus = dbp.nearby_bus_stops(lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_bus, limit=cfg.max_bus) if cfg.enable_bus else []
            groceries = dbp.nearby_groceries(lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_grocery, limit=cfg.max_grocery) if cfg.enable_grocery else []
            clothing = dbp.nearby_clothing(lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_clothing, limit=cfg.max_clothing) if cfg.enable_clothing else []
            data = {
                "listing": {
                    "id": ext.external_id,
                    "title": ext.title,
                    "price": ext.price,
                    "lat": ext.lat,
                    "lng": ext.lng,
                },
                "closest_stations": stations,
                "closest_metrobus": metrobus,
                "closest_bus_stops": bus,
                "closest_grocery_stores": groceries,
                "closest_clothing_stores": clothing,
            }
            # Summarize nearest distances in meters
            def _min_dist(arr):
                try:
                    return min(x.get("distance_m") for x in arr if x.get("distance_m") is not None)
                except (ValueError, TypeError):
                    return None
            nearest = {}
            if cfg.enable_metro:
                nearest["metro_m"] = _min_dist(stations)
            if cfg.enable_metrobus:
                nearest["metrobus_m"] = _min_dist(metrobus)
            if cfg.enable_bus:
                nearest["bus_m"] = _min_dist(bus)
            if cfg.enable_grocery:
                nearest["grocery_m"] = _min_dist(groceries)
            if cfg.enable_clothing:
                nearest["clothing_m"] = _min_dist(clothing)
            if cfg.enable_minibus:
                data["minibus"] = nearby_minibus_segments(
                    lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_minibus, limit=cfg.max_minibus
                )
                nearest["minibus_m"] = nearest_minibus_distance_m(lon=ext.lng, lat=ext.lat, max_radius_m=cfg.radius_minibus)
            if cfg.enable_bicycle:
                data["bicycle"] = nearby_bicycle_segments(
                    lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_bicycle, limit=cfg.max_bicycle
                )
                nearest["bicycle_m"] = nearest_bicycle_distance_m(lon=ext.lng, lat=ext.lat, max_radius_m=cfg.radius_bicycle)
            if cfg.enable_taxi:
                data["taxi"] = dbp.nearby_taxi_stands(
                    lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_taxi, limit=cfg.max_taxi
                )
                nearest["taxi_m"] = _min_dist(data["taxi"]) if data.get("taxi") else None
            if nearest:
                data["nearest_distances_m"] = nearest
            html = HTML_SKELETON.format(
                listing_id=ext.external_id,
                title=(ext.title or f"Listing #{ext.external_id}"),
                price=(f"{ext.price:,} TL" if ext.price else ""),
                data_json=json.dumps(data, ensure_ascii=False),
                icons_json=json.dumps(icons, ensure_ascii=False),
                preserve_aspect=json.dumps(bool(opts.get("preserve_icon_aspect"))),
                icon_max=24,
                listing_max=28,
                metrobus_max=18,
                taxi_max=18,
                grocery_max=18,
            )
            out_path = out_dir / f"listing_{ext.external_id}.html"
            out_path.write_text(html, encoding="utf-8")
            written += 1

        self.stdout.write(self.style.SUCCESS(f"Wrote {written} map file(s) to {out_dir}"))
