from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from ..models import LatLng, PlaceCandidate, PreferenceProfile, RecommendationItem
from ..storage import SqliteStore
from ..tools.map_provider import MapProvider


def _pref_match(place: PlaceCandidate, prefs: PreferenceProfile, query: str) -> Tuple[float, List[str]]:
    reasons: List[str] = []
    score = 1.0

    text = (place.name + " " + " ".join(place.tags) + " " + query).lower()

    if prefs.avoid_chain_brands and ("连锁" in place.tags or "chain" in text):
        score *= 0.7
        reasons.append("偏好：尽量避开连锁")

    for t in prefs.like_tags:
        if t and t.lower() in text:
            score *= 1.15
            reasons.append(f"匹配偏好：{t}")

    for t in prefs.dislike_tags:
        if t and t.lower() in text:
            score *= 0.6
            reasons.append(f"避免偏好：{t}")

    if "小众" in query and "小众" in place.tags:
        score *= 1.15
        reasons.append("符合“小众”诉求")

    if "咖啡" in query and ("咖啡馆" in place.tags or "咖啡" in place.name):
        score *= 1.12
        reasons.append("符合“咖啡”诉求")

    return score, reasons


def _price_fit(place: PlaceCandidate, budget: Optional[int]) -> Tuple[float, Optional[str]]:
    if budget is None or place.price_cny_per_person is None:
        return 1.0, None
    if place.price_cny_per_person <= budget:
        return 1.05, "预算内"
    # Soft penalty (not a hard filter) for MVP.
    return max(0.6, budget / max(1, place.price_cny_per_person)), "可能超预算"


@dataclass
class StrategyAgent:
    store: SqliteStore
    map_provider: MapProvider

    async def rank_food(
        self,
        *,
        user_id: str,
        origin: LatLng,
        query: str,
        candidates: List[PlaceCandidate],
        budget_cny_per_person: Optional[int],
        top_k: int,
    ) -> List[RecommendationItem]:
        prefs = self.store.get_preferences(user_id)
        if budget_cny_per_person is not None and prefs.budget_cny_per_person is None:
            prefs = prefs.model_copy(update={"budget_cny_per_person": budget_cny_per_person})

        scored: List[RecommendationItem] = []
        for c in candidates:
            base, reasons = _pref_match(c, prefs, query)

            eta = await self.map_provider.eta_minutes(origin, c.location)
            if eta is None:
                distance_factor = 1.0
            else:
                # 5 min is "perfect", 60+ min is heavily penalized
                distance_factor = max(0.25, min(1.2, 20.0 / max(5.0, float(eta))))

            novelty_factor = 0.75 if self.store.is_visited(user_id, c.place_id) else 1.15
            if novelty_factor < 1:
                reasons.append("去过：降低重复推荐")
            else:
                reasons.append("没去过：优先尝新")

            open_factor = 1.0
            if c.open_now is False:
                open_factor = 0.5
                reasons.append("可能未营业：降权")

            price_factor, price_reason = _price_fit(c, prefs.budget_cny_per_person)
            if price_reason:
                reasons.append(price_reason)

            score = base * distance_factor * novelty_factor * open_factor * price_factor
            scored.append(
                RecommendationItem(
                    place=c,
                    score=float(score),
                    reasons=reasons[:5],
                    eta_minutes=eta,
                )
            )

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[: max(1, min(top_k, 20))]

