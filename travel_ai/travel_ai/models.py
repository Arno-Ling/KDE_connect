from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class LatLng(BaseModel):
    lat: float
    lng: float


class PreferenceProfile(BaseModel):
    user_id: str
    avoid_chain_brands: bool = True
    like_tags: List[str] = Field(default_factory=list)
    dislike_tags: List[str] = Field(default_factory=list)
    max_drive_minutes_per_leg: int = 60
    budget_cny_per_person: Optional[int] = None


class VisitRecord(BaseModel):
    user_id: str
    place_id: str
    visited_at: datetime


class PlaceCandidate(BaseModel):
    place_id: str
    name: str
    location: LatLng
    address: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    rating: Optional[float] = None
    price_cny_per_person: Optional[int] = None
    open_now: Optional[bool] = None
    source: Literal["mock", "amap"] = "mock"
    raw: Dict[str, Any] = Field(default_factory=dict)


class RecommendFoodRequest(BaseModel):
    user_id: str
    lat: float
    lng: float
    query: str = "我饿了"
    budget_cny_per_person: Optional[int] = None
    top_k: int = 5


class RecommendationItem(BaseModel):
    place: PlaceCandidate
    score: float
    reasons: List[str]
    eta_minutes: Optional[int] = None


class RecommendFoodResponse(BaseModel):
    query: str
    origin: LatLng
    items: List[RecommendationItem]


class DayPlanRequest(BaseModel):
    user_id: str
    start_lat: float
    start_lng: float
    day: date = Field(default_factory=date.today)
    budget_cny_total: Optional[int] = None
    preferences_hint: Optional[str] = None


class PlanStop(BaseModel):
    kind: Literal["attraction", "food", "hotel", "rest"]
    place: PlaceCandidate
    arrive_eta_minutes: Optional[int] = None
    suggested_minutes: int = 60


class DayPlanResponse(BaseModel):
    day: date
    start: LatLng
    stops: List[PlanStop]
    notes: List[str] = Field(default_factory=list)

