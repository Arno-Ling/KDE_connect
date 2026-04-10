from __future__ import annotations

from fastapi import FastAPI

from .agents import InformationAgent, StrategyAgent
from .config import load_settings
from .gateway import Gateway
from .models import (
    DayPlanRequest,
    DayPlanResponse,
    PreferenceProfile,
    RecommendFoodRequest,
    RecommendFoodResponse,
)
from .storage import SqliteStore
from .tools import AMapProvider, MockMapProvider


def build_app() -> FastAPI:
    settings = load_settings()
    store = SqliteStore(settings.database_path)
    store.init()

    map_provider = MockMapProvider()
    if settings.amap_key:
        map_provider = AMapProvider(settings.amap_key)

    info_agent = InformationAgent(map_provider=map_provider)
    strategy_agent = StrategyAgent(store=store, map_provider=map_provider)
    gateway = Gateway(store=store, info_agent=info_agent, strategy_agent=strategy_agent)

    app = FastAPI(title="travel_ai", version="0.1.0")

    @app.get("/health")
    async def health() -> dict:
        return {"ok": True}

    @app.post("/v1/preferences", response_model=PreferenceProfile)
    async def upsert_preferences(profile: PreferenceProfile) -> PreferenceProfile:
        store.upsert_preferences(profile)
        return store.get_preferences(profile.user_id)

    @app.post("/v1/recommend/food", response_model=RecommendFoodResponse)
    async def recommend_food(req: RecommendFoodRequest) -> RecommendFoodResponse:
        return await gateway.recommend_food(req)

    @app.post("/v1/plan/day", response_model=DayPlanResponse)
    async def plan_day(req: DayPlanRequest) -> DayPlanResponse:
        return await gateway.plan_day(req)

    return app


app = build_app()

