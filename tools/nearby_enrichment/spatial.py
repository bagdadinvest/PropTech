import math


def haversine_distance_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Return great-circle distance in meters between two lon/lat points.

    Uses WGS84 mean earth radius. Accurate enough for neighborhood distances.
    """
    R = 6371008.8  # meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def within_radius_m(lon: float, lat: float, lon2: float, lat2: float, radius_m: float) -> bool:
    return haversine_distance_m(lon, lat, lon2, lat2) <= radius_m

