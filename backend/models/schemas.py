from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class FoodOption(BaseModel):
    name: str
    type: Literal["pantry", "store", "delivery"]
    cost_tier: Literal["free", "low", "market"]
    est_cost: str
    distance_mi: float | None = None
    transit_accessible: bool
    languages: list[str]
    id_required: bool
    cold_storage: bool
    hours: str
    address: str
    cuisine_tags: list[str] = Field(default_factory=list)


class DropLocation(BaseModel):
    name: str
    address: str
    routing_score: float
    reason: str


class ProduceAlert(BaseModel):
    active: bool
    pounds: int | None = None
    expires_in_hrs: int | None = None
    item: str | None = None
    top_drop_locations: list[DropLocation] = Field(default_factory=list)


class DeliveryOption(BaseModel):
    name: str
    snap_accepted: bool
    ebt_accepted: bool
    delivery_fee: float
    order_minimum: float
    estimated_weekly_total: float
    same_day: bool
    cost_tier: Literal["free", "low", "market"]
    serves_zip: bool
    notes: str
    market_rate: float | None = None
    subsidy_applied: float | None = None
    final_cost: float | None = None
    subsidy_label: str | None = None


class BatchedDelivery(BaseModel):
    cost_per_delivery: float
    estimated_hrs: int
    snap_accepted: bool = True
    ebt_accepted: bool = True
    description: str
    batch_density: int


class VoteZone(BaseModel):
    zip: str
    need_score: int
    spanish_dominant: bool
    label: str


class CommunityVote(BaseModel):
    active: bool = True
    deadline: str
    zones: list[VoteZone] = Field(default_factory=list)
    total_zones: int = 2


class OptionsResponse(BaseModel):
    zip: str
    need_score: int
    need_score_breakdown: dict[str, float] = Field(default_factory=dict)
    options: list[FoodOption]
    produce_alert: ProduceAlert
    delivery_necessity_flag: bool = False
    delivery_options: list[DeliveryOption] = Field(default_factory=list)
    batched_delivery: BatchedDelivery | None = None
    community_vote: CommunityVote | None = None


class AlertsResponse(BaseModel):
    active: bool
    pounds: int | None = None
    expires_in_hrs: int | None = None
    item: str | None = None
    top_drop_locations: list[DropLocation] = Field(default_factory=list)


class VoteRequest(BaseModel):
    name: str
    zip: str
    support: bool


class VoteResponse(BaseModel):
    status: str
    message: str


class ParseQueryRequest(BaseModel):
    query: str = Field(..., max_length=500)


class ParseQueryResponse(BaseModel):
    zip: str | None
    confidence: Literal["high", "low"] | None = None
    interpreted_as: str | None = None
    error: str | None = None
