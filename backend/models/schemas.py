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


class OptionsResponse(BaseModel):
    zip: str
    need_score: int
    options: list[FoodOption]
    produce_alert: ProduceAlert


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
