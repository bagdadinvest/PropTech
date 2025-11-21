from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.core.management.base import BaseCommand, CommandParser

from listings.models import ExternalListing, MapGenerationConfig
from tools.nearby_enrichment import db_providers as dbp
from tools.nearby_enrichment.minibus import nearest_minibus_distance_m
from tools.nearby_enrichment.bicycle import nearest_bicycle_distance_m


def _min_dist(arr: Optional[List[Dict[str, Any]]]) -> Optional[float]:
    if not arr:
        return None
    try:
        return min(x.get("distance_m") for x in arr if x.get("distance_m") is not None)
    except (ValueError, TypeError):
        return None


class Command(BaseCommand):
    help = "Compute and persist nearest distances (meters) for ExternalListing per enabled layer."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--source", default="coralcity", help="External source key")
        parser.add_argument("--listing-id", help="External listing id to process. If omitted, use --all or --limit")
        parser.add_argument("--all", action="store_true", help="Process all listings of the source")
        parser.add_argument("--limit", type=int, default=200, help="When not using --listing-id, cap number of listings")

    def handle(self, *args, **opts):
        source = opts["source"]
        cfg = MapGenerationConfig.get_config()

        if opts.get("listing_id"):
            qs = ExternalListing.objects.filter(source=source, external_id=str(opts["listing_id"]))
        elif opts.get("all"):
            qs = ExternalListing.objects.filter(source=source).order_by("-fetched_at")
        else:
            qs = ExternalListing.objects.filter(source=source).order_by("-fetched_at")[: opts["limit"]]

        updated = 0
        for ext in qs:
            nearest: Dict[str, Any] = {}
            # DB-backed layers use provider distance_m
            if cfg.enable_metro:
                nearest["metro_m"] = _min_dist(
                    dbp.nearby_metro_stations(lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_metro, limit=cfg.max_metro)
                )
            if cfg.enable_metrobus:
                nearest["metrobus_m"] = _min_dist(
                    dbp.nearby_metrobus_stations(lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_metrobus, limit=cfg.max_metrobus)
                )
            if cfg.enable_bus:
                nearest["bus_m"] = _min_dist(
                    dbp.nearby_bus_stops(lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_bus, limit=cfg.max_bus)
                )
            if cfg.enable_grocery:
                nearest["grocery_m"] = _min_dist(
                    dbp.nearby_groceries(lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_grocery, limit=cfg.max_grocery)
                )
            if cfg.enable_clothing:
                nearest["clothing_m"] = _min_dist(
                    dbp.nearby_clothing(lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_clothing, limit=cfg.max_clothing)
                )
            if cfg.enable_malls:
                nearest["malls_m"] = _min_dist(
                    dbp.nearby_malls(lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_malls, limit=cfg.max_malls)
                )
            if cfg.enable_parks:
                nearest["parks_m"] = _min_dist(
                    dbp.nearby_parks(lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_parks, limit=cfg.max_parks)
                )
            if cfg.enable_taxi:
                nearest["taxi_m"] = _min_dist(
                    dbp.nearby_taxi_stands(lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_taxi, limit=cfg.max_taxi)
                )
            # File-backed layers compute geometry distance
            if cfg.enable_minibus:
                nearest["minibus_m"] = nearest_minibus_distance_m(lon=ext.lng, lat=ext.lat, max_radius_m=cfg.radius_minibus)
            if cfg.enable_bicycle:
                nearest["bicycle_m"] = nearest_bicycle_distance_m(lon=ext.lng, lat=ext.lat, max_radius_m=cfg.radius_bicycle)

            ext.nearest_distances_m = {k: (float(v) if v is not None else None) for k, v in nearest.items()}
            ext.save(update_fields=["nearest_distances_m", "updated_at"])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"Updated nearest distances for {updated} listing(s)."))

