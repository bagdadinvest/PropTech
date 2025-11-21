from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

from .spatial import haversine_distance_m, within_radius_m


BASE_API_DIR = Path("distill_out/simplified/api")


def _load_geojson_features(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("features", [])


def _nearest_from_features(
    features: Iterable[Dict[str, Any]],
    *,
    lon: float,
    lat: float,
    radius_m: float,
    limit: int,
    transform_item: Optional[Callable[[Dict[str, Any], float], Dict[str, Any]]] = None,
    predicate: Optional[Callable[[Dict[str, Any]], bool]] = None,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for feat in features:
        if predicate is not None and not predicate(feat):
            continue
        geom = feat.get("geometry", {})
        if geom.get("type") != "Point":
            continue
        coords = geom.get("coordinates", None)
        if not coords or len(coords) < 2:
            continue
        flon, flat = float(coords[0]), float(coords[1])
        if not within_radius_m(lon, lat, flon, flat, radius_m):
            continue
        dist = haversine_distance_m(lon, lat, flon, flat)
        if transform_item is None:
            props = feat.get("properties", {})
            item = {
                "id": props.get("id"),
                "name": props.get("name"),
                "distance_m": dist,
                "location": {
                    "type": "Point",
                    "coordinates": [flon, flat],
                },
            }
        else:
            item = transform_item(feat, dist)
        rows.append(item)

    rows.sort(key=lambda r: r.get("distance_m", float("inf")))
    return rows[:limit]


def fetch_nearby_metro_stations(
    *, lon: float, lat: float, radius_m: float, limit: int = 3
) -> List[Dict[str, Any]]:
    """
    Fetch nearby metro stations. In offline mode, use local fallback file.

    Plug API here:
    - Istanbul Open Data WFS/REST with spatial filter (buffer/bbox/nearest)
    - e.g., CQL_FILTER=DWITHIN(geom, POINT(lon lat), radius, meters)
    """
    path = BASE_API_DIR / "metro_stations.geojson"
    feats = _load_geojson_features(path)
    return _nearest_from_features(feats, lon=lon, lat=lat, radius_m=radius_m, limit=limit)


def fetch_nearby_stores(
    *,
    lon: float,
    lat: float,
    radius_m: float,
    store_type: str,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """
    Fetch nearby stores by store_type (e.g., "grocery", "clothing").

    Offline fallback reads distill_out/simplified/api/stores.geojson and filters by `store_type`.
    """
    path = BASE_API_DIR / "stores.geojson"

    def pred(feat: Dict[str, Any]) -> bool:
        props = feat.get("properties", {})
        return props.get("store_type") == store_type

    feats = _load_geojson_features(path)

    def transform(feat: Dict[str, Any], dist: float) -> Dict[str, Any]:
        props = feat.get("properties", {})
        coords = feat.get("geometry", {}).get("coordinates", [None, None])
        return {
            "id": props.get("id"),
            "name": props.get("name"),
            "distance_m": dist,
            "location": {
                "type": "Point",
                "coordinates": [float(coords[0]), float(coords[1])],
            },
        }

    return _nearest_from_features(
        feats,
        lon=lon,
        lat=lat,
        radius_m=radius_m,
        limit=limit,
        transform_item=transform,
        predicate=pred,
    )

