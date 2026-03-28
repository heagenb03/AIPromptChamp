"""GET /api/alerts — supply alert + produce routing."""
from __future__ import annotations

from fastapi import APIRouter

from backend.data.cache import AppCache
from backend.models.schemas import AlertsResponse, DropLocation, VoteRequest, VoteResponse

router = APIRouter()


@router.get("/alerts", response_model=AlertsResponse)
def get_alerts() -> AlertsResponse:
    supply = AppCache.supply_alerts

    if not supply.get("active"):
        return AlertsResponse(active=False)

    from backend.ml.produce_routing import top_drop_locations
    drop_locs = top_drop_locations(n=3)

    return AlertsResponse(
        active=True,
        pounds=supply.get("pounds"),
        expires_in_hrs=supply.get("expires_in_hrs"),
        item=supply.get("item", "fresh produce"),
        top_drop_locations=[
            DropLocation(
                name=loc.name,
                address=loc.address,
                routing_score=loc.routing_score,
                reason=loc.reason,
            )
            for loc in drop_locs
        ],
    )


@router.post("/vote", response_model=VoteResponse)
def submit_vote(body: VoteRequest) -> VoteResponse:
    """Community vote stub — records the vote and returns confirmation."""
    # In a real app this would persist to a DB; for the demo it's a no-op
    return VoteResponse(
        status="recorded",
        message="Thank you for your vote!",
    )
