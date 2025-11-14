from typing import Any, Dict, List
from django.http import JsonResponse, HttpRequest
from .models import MetroStation, BusStop


def metro_stations_geojson(request: HttpRequest) -> JsonResponse:
    features: List[Dict[str, Any]] = []
    for st in MetroStation.objects.all():
        geom = st.location
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [geom.x, geom.y]},
                "properties": {"id": st.id, "name": st.name},
            }
        )
    return JsonResponse({"type": "FeatureCollection", "features": features})


def transit_geojson(request: HttpRequest) -> JsonResponse:
    features: List[Dict[str, Any]] = []
    # Metro
    for st in MetroStation.objects.all():
        geom = st.location
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [geom.x, geom.y]},
                "properties": {"id": st.id, "name": st.name, "mode": "metro"},
            }
        )
    # Bus
    for bs in BusStop.objects.all():
        geom = bs.location
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [geom.x, geom.y]},
                "properties": {"id": bs.id, "name": bs.name, "mode": "bus"},
            }
        )
    return JsonResponse({"type": "FeatureCollection", "features": features})
