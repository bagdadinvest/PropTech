from __future__ import annotations

import json
from typing import Any, Dict, List
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandParser
from django.contrib.gis.geos import Point

from listings.models import ExternalListing


def _fetch_json(url: str, params: Dict[str, Any] | None = None, headers: Dict[str, str] | None = None) -> Any:
    full_url = url
    if params:
        sep = "&" if ("?" in full_url) else "?"
        full_url = f"{full_url}{sep}{urlencode(params, doseq=True)}"
    req = Request(full_url, headers=headers or {})
    with urlopen(req, timeout=30) as resp:
        data = resp.read()
    return json.loads(data.decode("utf-8"))


class Command(BaseCommand):
    help = "Sync external listings into ExternalListing table (upsert by source+external_id)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--api-url", required=True, help="Endpoint returning list or {results:[...]}")
        parser.add_argument("--source", default="coralcity", help="Source key to tag records with")
        parser.add_argument("--limit", type=int, default=24, help="Limit rows to import")
        parser.add_argument("--bbox", help="minLon,minLat,maxLon,maxLat to filter upstream")
        parser.add_argument("--auth", help="Authorization header value (Token/Bearer)")

    def handle(self, *args, **options):
        api_url: str = options["api_url"]
        source: str = options["source"]
        limit: int = options["limit"]
        bbox: str | None = options.get("bbox")
        headers: Dict[str, str] = {}
        if options.get("auth"):
            headers["Authorization"] = options["auth"]

        params: Dict[str, Any] = {"limit": max(limit, 1)}
        if bbox:
            params["bbox"] = bbox

        payload = _fetch_json(api_url, params=params, headers=headers)
        if isinstance(payload, dict) and isinstance(payload.get("results"), list):
            rows: List[Dict[str, Any]] = payload["results"]
        elif isinstance(payload, list):
            rows = payload
        else:
            self.stderr.write("Unsupported response shape; expected list or {'results': [...]}.")
            return 2

        imported = 0
        for r in rows[:limit]:
            ext_id = str(r.get("id"))
            if not ext_id:
                continue
            lat = r.get("lat")
            lng = r.get("lng")
            if lat is None or lng is None:
                continue
            obj, created = ExternalListing.objects.update_or_create(
                source=source,
                external_id=ext_id,
                defaults={
                    "title": r.get("title") or "",
                    "price": r.get("price"),
                    "deal_type": r.get("deal_type") or "",
                    "city": r.get("city") or "",
                    "state": r.get("state") or "",
                    "url": r.get("url") or "",
                    "original_url": r.get("original_url") or "",
                    "lat": float(lat),
                    "lng": float(lng),
                    "location": Point(float(lng), float(lat), srid=4326),
                    "payload": r,
                },
            )
            imported += 1
        self.stdout.write(self.style.SUCCESS(f"Synced {imported} listings into ExternalListing."))

