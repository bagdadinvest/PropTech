from __future__ import annotations

from typing import Any, Dict, List

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point


def _serialize(item, dist_field: str = "distance") -> Dict[str, Any]:
    loc = getattr(item, "location")
    coords = [loc.x, loc.y]
    return {
        "id": getattr(item, "id", None),
        "name": getattr(item, "name", ""),
        "distance_m": float(getattr(item, dist_field).m),
        "location": {"type": "Point", "coordinates": coords},
    }


def nearby_metro_stations(*, lon: float, lat: float, radius_m: int, limit: int = 6) -> List[Dict[str, Any]]:
    try:
        from transit_layer.models import MetroStation
    except Exception:
        return []
    ref = Point(lon, lat, srid=4326)
    qs = (
        MetroStation.objects.annotate(distance=Distance("location", ref))
        .filter(location__distance_lte=(ref, radius_m))
        .order_by("distance")[:limit]
    )
    return [_serialize(o) for o in qs]


def nearby_metrobus_stations(*, lon: float, lat: float, radius_m: int, limit: int = 6) -> List[Dict[str, Any]]:
    try:
        from transit_layer.models import MetrobusStation
    except Exception:
        return []
    ref = Point(lon, lat, srid=4326)
    qs = (
        MetrobusStation.objects.annotate(distance=Distance("location", ref))
        .filter(location__distance_lte=(ref, radius_m))
        .order_by("distance")[:limit]
    )
    return [_serialize(o) for o in qs]


def nearby_bus_stops(*, lon: float, lat: float, radius_m: int, limit: int = 8) -> List[Dict[str, Any]]:
    try:
        from transit_layer.models import BusStop
    except Exception:
        return []
    ref = Point(lon, lat, srid=4326)
    qs = (
        BusStop.objects.annotate(distance=Distance("location", ref))
        .filter(location__distance_lte=(ref, radius_m))
        .order_by("distance")[:limit]
    )
    return [_serialize(o) for o in qs]


def nearby_groceries(*, lon: float, lat: float, radius_m: int, limit: int = 6) -> List[Dict[str, Any]]:
    try:
        from stores_layer.models import Grocery
    except Exception:
        return []
    ref = Point(lon, lat, srid=4326)
    qs = (
        Grocery.objects.annotate(distance=Distance("location", ref))
        .filter(location__distance_lte=(ref, radius_m))
        .order_by("distance")[:limit]
    )
    return [_serialize(o) for o in qs]


def nearby_clothing(*, lon: float, lat: float, radius_m: int, limit: int = 6) -> List[Dict[str, Any]]:
    try:
        from stores_layer.models import Clothing
    except Exception:
        return []
    ref = Point(lon, lat, srid=4326)
    qs = (
        Clothing.objects.annotate(distance=Distance("location", ref))
        .filter(location__distance_lte=(ref, radius_m))
        .order_by("distance")[:limit]
    )
    return [_serialize(o) for o in qs]


def nearby_malls(*, lon: float, lat: float, radius_m: int, limit: int = 6) -> List[Dict[str, Any]]:
    try:
        from stores_layer.models import Mall
    except Exception:
        return []
    ref = Point(lon, lat, srid=4326)
    qs = (
        Mall.objects.annotate(distance=Distance("location", ref))
        .filter(location__distance_lte=(ref, radius_m))
        .order_by("distance")[:limit]
    )
    return [_serialize(o) for o in qs]


def nearby_parks(*, lon: float, lat: float, radius_m: int, limit: int = 6) -> List[Dict[str, Any]]:
    try:
        from stores_layer.models import Park
    except Exception:
        return []
    ref = Point(lon, lat, srid=4326)
    qs = (
        Park.objects.annotate(distance=Distance("location", ref))
        .filter(location__distance_lte=(ref, radius_m))
        .order_by("distance")[:limit]
    )
    return [_serialize(o) for o in qs]


def nearby_taxi_stands(*, lon: float, lat: float, radius_m: int, limit: int = 8) -> List[Dict[str, Any]]:
    try:
        from transit_layer.models import TaxiStand
    except Exception:
        return []
    ref = Point(lon, lat, srid=4326)
    qs = (
        TaxiStand.objects.annotate(distance=Distance("location", ref))
        .filter(location__distance_lte=(ref, radius_m))
        .order_by("distance")[:limit]
    )
    return [_serialize(o) for o in qs]
