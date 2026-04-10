from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..models import LatLng, PlaceCandidate
from ..tools.map_provider import MapProvider


@dataclass
class InformationAgent:
    map_provider: MapProvider

    async def find_food_candidates(
        self, *, origin: LatLng, query: str, limit: int = 20
    ) -> List[PlaceCandidate]:
        # Keep this agent "tool-heavy": it just gathers candidates.
        return await self.map_provider.search_food(origin, query, limit=limit)

