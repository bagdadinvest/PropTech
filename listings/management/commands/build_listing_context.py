from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from django.core.management.base import BaseCommand, CommandParser

from listings.models import ExternalListing, MapGenerationConfig
from tools.nearby_enrichment import db_providers as dbp
from tools.nearby_enrichment.minibus import nearby_minibus_segments, nearest_minibus_distance_m
from tools.nearby_enrichment.bicycle import nearby_bicycle_segments, nearest_bicycle_distance_m


def _serialize_listing(ext: ExternalListing) -> Dict[str, Any]:
    return {
        "id": ext.external_id,
        "title": ext.title,
        "lat": ext.lat,
        "lng": ext.lng,
    }


class Command(BaseCommand):
    help = "Build minimal JSON context (name + point + distance) per listing, based on MapGenerationConfig."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--source", default="coralcity", help="External source key")
        parser.add_argument("--listing-id", help="External listing id to build for. If omitted, use --all or --limit")
        parser.add_argument("--all", action="store_true", help="Build for all listings of the source")
        parser.add_argument("--limit", type=int, default=24, help="When not using --listing-id, cap number of listings")
        parser.add_argument("--out-dir", default="distill_out/simplified/contexts", help="Output directory for JSON files")
        parser.add_argument("--combined", action="store_true", help="Also write a combined contexts.json aggregating all")

    def handle(self, *args, **opts):
        source = opts["source"]
        out_dir = Path(opts["out_dir"]) ; out_dir.mkdir(parents=True, exist_ok=True)
        cfg = MapGenerationConfig.get_config()

        if opts.get("listing_id"):
            qs = ExternalListing.objects.filter(source=source, external_id=str(opts["listing_id"]))
        elif opts.get("all"):
            qs = ExternalListing.objects.filter(source=source).order_by("-fetched_at")
        else:
            qs = ExternalListing.objects.filter(source=source).order_by("-fetched_at")[: opts["limit"]]

        written = 0
        combined: List[Dict[str, Any]] = []

        for ext in qs:
            layers: Dict[str, Any] = {"listing": _serialize_listing(ext)}

            if cfg.enable_metro:
                layers["metro"] = dbp.nearby_metro_stations(
                    lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_metro, limit=cfg.max_metro
                )
            if cfg.enable_metrobus:
                layers["metrobus"] = dbp.nearby_metrobus_stations(
                    lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_metrobus, limit=cfg.max_metrobus
                )
            if cfg.enable_bus:
                layers["bus"] = dbp.nearby_bus_stops(
                    lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_bus, limit=cfg.max_bus
                )
            if cfg.enable_grocery:
                layers["grocery"] = dbp.nearby_groceries(
                    lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_grocery, limit=cfg.max_grocery
                )
            if cfg.enable_clothing:
                layers["clothing"] = dbp.nearby_clothing(
                    lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_clothing, limit=cfg.max_clothing
                )
            if cfg.enable_malls:
                layers["malls"] = dbp.nearby_malls(
                    lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_malls, limit=cfg.max_malls
                )
            if cfg.enable_parks:
                layers["parks"] = dbp.nearby_parks(
                    lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_parks, limit=cfg.max_parks
                )
            # Pharmacy placeholder: integrate when a model/provider exists
            if cfg.enable_minibus:
                layers["minibus"] = nearby_minibus_segments(
                    lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_minibus, limit=cfg.max_minibus
                )
            if cfg.enable_taxi:
                layers["taxi"] = dbp.nearby_taxi_stands(
                    lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_taxi, limit=cfg.max_taxi
                )
            if cfg.enable_bicycle:
                layers["bicycle"] = nearby_bicycle_segments(
                    lon=ext.lng, lat=ext.lat, radius_m=cfg.radius_bicycle, limit=cfg.max_bicycle
                )

            # Summarize nearest distances (meters) per enabled layer
            def _min_dist(arr):
                try:
                    return min(x.get("distance_m") for x in arr if x.get("distance_m") is not None)
                except (ValueError, TypeError):
                    return None

            nearest: Dict[str, Any] = {}
            if cfg.enable_metro:
                nearest["metro_m"] = _min_dist(layers.get("metro", []))
            if cfg.enable_metrobus:
                nearest["metrobus_m"] = _min_dist(layers.get("metrobus", []))
            if cfg.enable_bus:
                nearest["bus_m"] = _min_dist(layers.get("bus", []))
            if cfg.enable_grocery:
                nearest["grocery_m"] = _min_dist(layers.get("grocery", []))
            if cfg.enable_clothing:
                nearest["clothing_m"] = _min_dist(layers.get("clothing", []))
            if cfg.enable_malls:
                nearest["malls_m"] = _min_dist(layers.get("malls", []))
            if cfg.enable_parks:
                nearest["parks_m"] = _min_dist(layers.get("parks", []))
            if cfg.enable_taxi:
                nearest["taxi_m"] = _min_dist(layers.get("taxi", []))
            if cfg.enable_minibus:
                # Use geometry-based distance for higher fidelity
                d = nearest_minibus_distance_m(lon=ext.lng, lat=ext.lat, max_radius_m=cfg.radius_minibus)
                nearest["minibus_m"] = d
            if cfg.enable_bicycle:
                d = nearest_bicycle_distance_m(lon=ext.lng, lat=ext.lat, max_radius_m=cfg.radius_bicycle)
                nearest["bicycle_m"] = d

            layers["nearest_distances_m"] = nearest

            out_path = out_dir / f"listing_{ext.external_id}_context.json"
            out_path.write_text(json.dumps(layers, ensure_ascii=False), encoding="utf-8")
            written += 1
            if opts.get("combined"):
                combined.append(layers)

        if opts.get("combined") and combined:
            (out_dir / "contexts.json").write_text(json.dumps(combined, ensure_ascii=False), encoding="utf-8")

        self.stdout.write(self.style.SUCCESS(f"Wrote {written} context file(s) to {out_dir}"))
