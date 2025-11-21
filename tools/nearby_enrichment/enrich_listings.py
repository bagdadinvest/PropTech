from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from .providers import fetch_nearby_metro_stations, fetch_nearby_stores


def _read_geojson(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_geojson(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def enrich(
    *,
    input_path: Path,
    output_path: Path,
    radius_m: int,
    limit_stations: int,
    limit_grocery: int,
    limit_clothing: int,
) -> Dict[str, Any]:
    src = _read_geojson(input_path)
    features = src.get("features", [])

    out_features: List[Dict[str, Any]] = []
    stats = {
        "num_listings": 0,
        "num_stations": 0,
        "num_grocery_stores": 0,
        "num_clothing_stores": 0,
    }

    for feat in features:
        geom = feat.get("geometry", {})
        if geom.get("type") != "Point":
            continue
        lon, lat = geom.get("coordinates", [None, None])
        if lon is None or lat is None:
            continue

        props = feat.get("properties", {})

        stations = fetch_nearby_metro_stations(
            lon=float(lon), lat=float(lat), radius_m=radius_m, limit=limit_stations
        )
        grocery = fetch_nearby_stores(
            lon=float(lon), lat=float(lat), radius_m=radius_m, store_type="grocery", limit=limit_grocery
        )
        clothing = fetch_nearby_stores(
            lon=float(lon), lat=float(lat), radius_m=radius_m, store_type="clothing", limit=limit_clothing
        )

        stats["num_listings"] += 1
        stats["num_stations"] += len(stations)
        stats["num_grocery_stores"] += len(grocery)
        stats["num_clothing_stores"] += len(clothing)

        out_props = {
            # Pass-through basic listing fields if present
            "id": props.get("id"),
            "title": props.get("title"),
            "price": props.get("price"),
            "size_sqm": props.get("size_sqm"),
            "image_url": props.get("image_url"),
            "images": props.get("images", []),
            # Enrichment
            "closest_stations": stations,
            "closest_grocery_stores": grocery,
            "closest_clothing_stores": clothing,
        }

        out_features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
            "properties": out_props,
        })

    result = {
        "type": "FeatureCollection",
        "features": out_features,
        "config": stats,
    }
    _write_geojson(output_path, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich listings with nearby POIs and output simplified GeoJSON.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("distill_out/simplified/api/listings.geojson"),
        help="Path to input listings GeoJSON (Point features).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("distill_out/simplified/api/listings-simplified.geojson"),
        help="Path to output simplified GeoJSON.",
    )
    parser.add_argument(
        "--radius-m",
        type=int,
        default=1200,
        help="Walking radius in meters to search for POIs.",
    )
    parser.add_argument("--stations", type=int, default=3, help="Max closest metro stations to include.")
    parser.add_argument("--grocery", type=int, default=3, help="Max closest grocery stores to include.")
    parser.add_argument("--clothing", type=int, default=3, help="Max closest clothing stores to include.")

    args = parser.parse_args()
    enrich(
        input_path=args.input,
        output_path=args.output,
        radius_m=args.radius_m,
        limit_stations=args.stations,
        limit_grocery=args.grocery,
        limit_clothing=args.clothing,
    )


if __name__ == "__main__":
    main()

