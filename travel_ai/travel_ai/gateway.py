from __future__ import annotations

from dataclasses import dataclass

from .agents.information_agent import InformationAgent
from .agents.strategy_agent import StrategyAgent
from .models import (
    DayPlanRequest,
    DayPlanResponse,
    LatLng,
    RecommendFoodRequest,
    RecommendFoodResponse,
)
from .storage import SqliteStore


@dataclass
class Gateway:
    store: SqliteStore
    info_agent: InformationAgent
    strategy_agent: StrategyAgent

    async def recommend_food(self, req: RecommendFoodRequest) -> RecommendFoodResponse:
        origin = LatLng(lat=req.lat, lng=req.lng)

        candidates = await self.info_agent.find_food_candidates(
            origin=origin, query=req.query, limit=20
        )

        # Cache raw candidates for future joins (e.g. plan generation)
        self.store.cache_places(candidates)

        items = await self.strategy_agent.rank_food(
            user_id=req.user_id,
            origin=origin,
            query=req.query,
            candidates=candidates,
            budget_cny_per_person=req.budget_cny_per_person,
            top_k=req.top_k,
        )

        return RecommendFoodResponse(query=req.query, origin=origin, items=items)

    async def plan_day(self, req: DayPlanRequest) -> DayPlanResponse:
        # MVP placeholder: reuse food recommendation as a simple stop.
        # This keeps an end-to-end API for iteration.
        origin = LatLng(lat=req.start_lat, lng=req.start_lng)

        food_req = RecommendFoodRequest(
            user_id=req.user_id,
            lat=req.start_lat,
            lng=req.start_lng,
            query=req.preferences_hint or "找一家评分高的本地餐馆",
            budget_cny_per_person=None,
            top_k=1,
        )
        food = await self.recommend_food(food_req)
        stops = []
        if food.items:
            stops.append(
                {
                    "kind": "food",
                    "place": food.items[0].place,
                    "arrive_eta_minutes": food.items[0].eta_minutes,
                    "suggested_minutes": 75,
                }
            )

        return DayPlanResponse(
            day=req.day,
            start=origin,
            stops=stops,  # pydantic will coerce dict -> model
            notes=[
                "这是 MVP 的 1 天游玩骨架：目前只演示“候选采集 + 排序 + 输出结构化计划”。",
                "下一步可以加入：景点候选、时间窗、驾驶时长上限、预算约束与动态重排。",
            ],
        )

