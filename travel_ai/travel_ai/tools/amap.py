from __future__ import annotations

from typing import List, Optional

import httpx

from ..models import LatLng, PlaceCandidate
from .map_provider import MapProvider


class AMapProvider(MapProvider):
    """
    AMap Web Service wrapper (optional).

    If you don't set AMAP_KEY, the app will fallback to MockMapProvider.
    """

    def __init__(self, key: str):
        self.key = key

    async def search_food(
        self,
        origin: LatLng,
        query: str,
        *,
        radius_m: int = 5000,
        limit: int = 20,
    ) -> List[PlaceCandidate]:
        # AMap "Around Search" (place around)
        # docs: https://lbs.amap.com/api/webservice/guide/api/search
        url = "https://restapi.amap.com/v3/place/around"
        params = {
            "key": self.key,
            "location": f"{origin.lng},{origin.lat}",
            "keywords": query,
            "types": "050000",  # dining
            "radius": str(radius_m),
            "sortrule": "distance",
            "offset": str(min(limit, 25)),
            "page": "1",
            "extensions": "base",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()

        pois = data.get("pois") or []
        out: List[PlaceCandidate] = []
        for p in pois[:limit]:
            loc = p.get("location") or ""
            try:
                lng_s, lat_s = loc.split(",")
                loc_ll = LatLng(lat=float(lat_s), lng=float(lng_s))
            except Exception:
                continue

            tags = []
            if p.get("type"):
                tags.extend([t.strip() for t in str(p["type"]).split(";") if t.strip()])

            out.append(
                PlaceCandidate(
                    place_id=str(p.get("id") or ""),
                    name=str(p.get("name") or ""),
                    location=loc_ll,
                    address=p.get("address") or None,
                    tags=tags,
                    rating=float(p["rating"]) if p.get("rating") not in (None, "", "[]") else None,
                    price_cny_per_person=int(float(p["cost"])) if p.get("cost") not in (None, "", "[]") else None,
                    open_now=None,
                    source="amap",
                    raw=p,
                )
            )
        return [x for x in out if x.place_id and x.name]

    async def eta_minutes(self, origin: LatLng, dest: LatLng) -> Optional[int]:
        # AMap driving direction
        # docs: https://lbs.amap.com/api/webservice/guide/api/direction
        url = "https://restapi.amap.com/v3/direction/driving"
        params = {
            "key": self.key,
            "origin": f"{origin.lng},{origin.lat}",
            "destination": f"{dest.lng},{dest.lat}",
            "extensions": "base",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()

        route = (data.get("route") or {})
        paths = route.get("paths") or []
        if not paths:
            return None
        duration_s = paths[0].get("duration")
        try:
            return max(1, int(int(duration_s) / 60))
        except Exception:
            return None

