from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _get_in(obj: Dict[str, Any], dotted: Optional[str]) -> Any:
    if not dotted:
        return None
    cur: Any = obj
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def _to_float(val: Any) -> Optional[float]:
    try:
        return float(val)
    except Exception:
        return None


@dataclass
class FieldMap:
    id: str = "id"
    lon: str = "longitude"
    lat: str = "latitude"
    title: Optional[str] = None
    price: Optional[str] = None
    size_sqm: Optional[str] = None
    image_url: Optional[str] = None
    images: Optional[str] = None  # expects list


def fetch_json(
    base_url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Any:
    url = base_url
    if params:
        qs = urlencode(params, doseq=True)
        sep = "&" if ("?" in url) else "?"
        url = f"{url}{sep}{qs}"
    req = Request(url, headers=headers or {})
    with urlopen(req, timeout=30) as resp:
        data = resp.read()
    return json.loads(data.decode("utf-8"))


def to_geojson(
    rows: Iterable[Dict[str, Any]],
    fmap: FieldMap,
    limit: int,
    sort_by: Optional[str] = None,
    sort_desc: bool = True,
) -> Dict[str, Any]:
    items = list(rows)
    if sort_by:
        items.sort(key=lambda r: _get_in(r, sort_by), reverse=sort_desc)
    if limit:
        items = items[:limit]

    features: List[Dict[str, Any]] = []
    for r in items:
        lon = _to_float(_get_in(r, fmap.lon))
        lat = _to_float(_get_in(r, fmap.lat))
        if lon is None or lat is None:
            continue
        props: Dict[str, Any] = {
            "id": _get_in(r, fmap.id),
        }
        if fmap.title:
            props["title"] = _get_in(r, fmap.title)
        if fmap.price:
            props["price"] = _get_in(r, fmap.price)
        if fmap.size_sqm:
            props["size_sqm"] = _get_in(r, fmap.size_sqm)
        if fmap.image_url:
            props["image_url"] = _get_in(r, fmap.image_url)
        if fmap.images:
            imgs = _get_in(r, fmap.images)
            if isinstance(imgs, list):
                props["images"] = imgs

        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": props,
            }
        )

    return {"type": "FeatureCollection", "features": features}


def write_geojson(path: str, data: Dict[str, Any]) -> None:
    from pathlib import Path

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch listing pinpoints from a Django (or any) API and write GeoJSON for the map."
    )
    parser.add_argument("--api-url", required=True, help="Base API endpoint returning JSON list or object with 'results'.")
    parser.add_argument("--param", action="append", default=[], help="Extra query param in key=value form. Repeatable.")
    parser.add_argument("--auth", help="Authorization header value (e.g., 'Token abc' or 'Bearer xyz').")
    parser.add_argument("--limit", type=int, default=24, help="Max listings to keep (default 24).")
    parser.add_argument("--sort-by", help="Dotted path to sort by before limiting (e.g., 'created_at').")
    parser.add_argument("--sort-asc", action="store_true", help="Sort ascending (default descending).")
    parser.add_argument("--output", default="distill_out/simplified/api/listings.geojson", help="Output path.")

    # Field mapping
    parser.add_argument("--id-field", default="id")
    parser.add_argument("--lon-field", default="longitude")
    parser.add_argument("--lat-field", default="latitude")
    parser.add_argument("--title-field")
    parser.add_argument("--price-field")
    parser.add_argument("--size-field")
    parser.add_argument("--image-url-field")
    parser.add_argument("--images-field")

    args = parser.parse_args()

    params: Dict[str, Any] = {}
    for kv in args.param:
        if "=" not in kv:
            print(f"Ignoring malformed --param '{kv}', expected key=value", file=sys.stderr)
            continue
        k, v = kv.split("=", 1)
        params[k] = v

    headers: Dict[str, str] = {}
    if args.auth:
        headers["Authorization"] = args.auth

    try:
        payload = fetch_json(args.api_url, params=params, headers=headers)
    except Exception as e:
        print(f"Fetch failed: {e}", file=sys.stderr)
        sys.exit(2)

    # Handle common response shapes
    if isinstance(payload, dict) and "results" in payload and isinstance(payload["results"], list):
        rows = payload["results"]
    elif isinstance(payload, list):
        rows = payload
    else:
        print("Unsupported response shape: expected list or {'results': [...]}.", file=sys.stderr)
        sys.exit(3)

    fmap = FieldMap(
        id=args.id_field,
        lon=args.lon_field,
        lat=args.lat_field,
        title=args.title_field,
        price=args.price_field,
        size_sqm=args.size_field,
        image_url=args.image_url_field,
        images=args.images_field,
    )

    geo = to_geojson(
        rows,
        fmap=fmap,
        limit=args.limit,
        sort_by=args.sort_by,
        sort_desc=not args.sort_asc,
    )
    write_geojson(args.output, geo)
    print(f"Wrote {len(geo.get('features', []))} features -> {args.output}")


if __name__ == "__main__":
    main()

