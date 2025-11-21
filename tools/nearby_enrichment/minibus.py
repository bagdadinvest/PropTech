from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.contrib.gis.geos import GEOSGeometry, Point


DEFAULT_MINIBUS_PATHS = [
    Path("Minibus Lines Data"),
    Path("data/minibus_lines.geojson"),
]


@lru_cache(maxsize=1)
def _load_minibus_geojson() -> List[Dict[str, Any]]:
    override = os.environ.get("MINIBUS_GEOJSON_PATH")
    paths = [Path(override)] if override else DEFAULT_MINIBUS_PATHS
    for p in paths:
        if p.exists():
            with p.open("r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
            feats = data.get("features", [])
            return feats
    return []


def _to_geom(feat: Dict[str, Any]) -> GEOSGeometry | None:
    geom = feat.get("geometry")
    if not geom:
        return None
    try:
        g = GEOSGeometry(json.dumps(geom))
        g.srid = 4326
        return g
    except Exception:
        return None


def nearby_minibus_segments(*, lon: float, lat: float, radius_m: int, limit: int) -> List[Dict[str, Any]]:
    feats = _load_minibus_geojson()
    if not feats:
        return []

    # Buffer around the listing point in meters (project to 3857 for metric buffering)
    center = Point(lon, lat, srid=4326)
    try:
        center_3857 = center.transform(3857, clone=True)
    except Exception:
        # If transform not available, fallback to no clipping (just intersects by bbox)
        center_3857 = center
    buffer_geom = center_3857.buffer(radius_m)

    results: List[Dict[str, Any]] = []
    for feat in feats:
        g = _to_geom(feat)
        if g is None:
            continue
        try:
            g_3857 = g.transform(3857, clone=True)
            if not g_3857.intersects(buffer_geom):
                continue
            clipped_3857 = g_3857.intersection(buffer_geom)
            clipped = clipped_3857.transform(4326, clone=True)
            geom_geojson = json.loads(clipped.geojson)
        except Exception:
            # Fallback: include entire geometry if clipping fails
            geom_geojson = feat.get("geometry")

        props = feat.get("properties", {})
        line_id = props.get("HATNO") or props.get("id") or props.get("OBJECTID")
        name = props.get("HAT_ADI") or props.get("GUZERGAH") or str(line_id)

        results.append({
            "id": line_id,
            "name": name,
            "geometry": geom_geojson,
        })
        if limit and len(results) >= limit:
            break

    return results

def nearest_minibus_distance_m(*, lon: float, lat: float, max_radius_m: Optional[int] = None) -> Optional[float]:
    """
    Compute distance in meters from the given point to the nearest minibus line segment.
    Uses in-memory GeoJSON and GEOS; transforms to EPSG:3857 for metric distance.
    If max_radius_m is provided, restricts consideration to that buffer and returns None if none intersect.
    """
    feats = _load_minibus_geojson()
    if not feats:
        return None

    center = Point(lon, lat, srid=4326)
    try:
        center_3857 = center.transform(3857, clone=True)
    except Exception:
        center_3857 = center
    buf = center_3857.buffer(max_radius_m) if max_radius_m else None

    best: Optional[float] = None
    for feat in feats:
        g = _to_geom(feat)
        if g is None:
            continue
        try:
            g_3857 = g.transform(3857, clone=True)
            if buf is not None and not g_3857.intersects(buf):
                continue
            d = g_3857.distance(center_3857)
        except Exception:
            d = g.distance(center)
        if best is None or d < best:
            best = d
    return float(best) if best is not None else None
