from typing import Any, Dict, List
from django.http import JsonResponse, HttpRequest
from .models import Clothing, Grocery


def stores_geojson(request: HttpRequest) -> JsonResponse:
    """
    Returns all stores (Clothing and Grocery) as a GeoJSON FeatureCollection.
    Each feature includes store name and type.
    """
    features: List[Dict[str, Any]] = []
    
    # Clothing stores
    for store in Clothing.objects.all():
        geom = store.location
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [geom.x, geom.y]},
                "properties": {
                    "id": store.id,
                    "name": store.name,
                    "store_type": "clothing",
                },
            }
        )
    
    # Grocery stores
    for store in Grocery.objects.all():
        geom = store.location
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [geom.x, geom.y]},
                "properties": {
                    "id": store.id,
                    "name": store.name,
                    "store_type": "grocery",
                },
            }
        )
    
    return JsonResponse({"type": "FeatureCollection", "features": features})
