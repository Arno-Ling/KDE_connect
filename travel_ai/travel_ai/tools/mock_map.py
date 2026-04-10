from __future__ import annotations

import math
import random
from typing import List, Optional

from ..models import LatLng, PlaceCandidate
from .map_provider import MapProvider


def _haversine_km(a: LatLng, b: LatLng) -> float:
    r = 6371.0
    lat1, lon1 = math.radians(a.lat), math.radians(a.lng)
    lat2, lon2 = math.radians(b.lat), math.radians(b.lng)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    x = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(x))


class MockMapProvider(MapProvider):
    async def search_food(
        self,
        origin: LatLng,
        query: str,
        *,
        radius_m: int = 5000,
        limit: int = 20,
    ) -> List[PlaceCandidate]:
        random.seed(f"{origin.lat:.4f},{origin.lng:.4f}:{query}")
        tags_pool = [
            "小众",
            "咖啡馆",
            "本地口味",
            "夜宵",
            "景观位",
            "亲子友好",
            "安静",
            "连锁",
        ]

        out: List[PlaceCandidate] = []
        for i in range(limit):
            dlat = (random.random() - 0.5) * 0.06
            dlng = (random.random() - 0.5) * 0.06
            loc = LatLng(lat=origin.lat + dlat, lng=origin.lng + dlng)
            tags = random.sample(tags_pool, k=random.randint(2, 4))
            out.append(
                PlaceCandidate(
                    place_id=f"mock_food_{i}",
                    name=f"{random.choice(['山野', '拐角', '慢煮', '木窗', '巷子'])}{random.choice(['咖啡', '小馆', '食堂', '面馆', '茶铺'])}{i}",
                    location=loc,
                    address="(mock) 附近某条路",
                    tags=tags,
                    rating=round(random.uniform(3.6, 4.9), 1),
                    price_cny_per_person=random.choice([25, 35, 48, 58, 68, 88, 108]),
                    open_now=random.choice([True, True, True, False]),
                    source="mock",
                    raw={"radius_m": radius_m, "query": query},
                )
            )
        return out

    async def eta_minutes(self, origin: LatLng, dest: LatLng) -> Optional[int]:
        km = _haversine_km(origin, dest)
        # Rough city driving: 25 km/h, add some randomness.
        minutes = int((km / 25.0) * 60.0)
        return max(1, minutes)

