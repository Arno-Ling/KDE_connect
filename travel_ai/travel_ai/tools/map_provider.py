from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from ..models import LatLng, PlaceCandidate


class MapProvider(ABC):
    @abstractmethod
    async def search_food(
        self,
        origin: LatLng,
        query: str,
        *,
        radius_m: int = 5000,
        limit: int = 20,
    ) -> List[PlaceCandidate]:
        raise NotImplementedError

    @abstractmethod
    async def eta_minutes(self, origin: LatLng, dest: LatLng) -> Optional[int]:
        raise NotImplementedError

