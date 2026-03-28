"""GET /api/options?zip=XXXXX — core endpoint."""
from __future__ import annotations

import math
import logging

from fastapi import APIRouter, HTTPException, Query

from backend.data.cache import AppCache
from backend.ml.need_score import get_score
from backend.models.schemas import (
    DropLocation,
    FoodOption,
    OptionsResponse,
    ProduceAlert,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# KC ZIP codes are 641xx
_VALID_ZIP_PREFIX = "641"
_DEFAULT_RADIUS_MI = 10.0

# Lat/lng center points per ZIP for distance calculation
# These approximate centroids for common KC ZIPs
_ZIP_CENTERS: dict[str, tuple[float, float]] = {
    "64101": (39.1031, -94.5761),
    "64105": (39.1016, -94.5782),
    "64106": (39.1001, -94.5710),
    "64108": (39.0955, -94.5768),
    "64109": (39.0771, -94.5636),
    "64110": (39.0618, -94.5807),
    "64111": (39.0618, -94.5807),
    "64112": (39.0432, -94.5966),
    "64113": (39.0182, -94.5966),
    "64114": (38.9982, -94.5966),
    "64120": (39.1152, -94.5178),
    "64123": (39.1152, -94.5499),
    "64124": (39.1001, -94.5499),
    "64125": (39.1001, -94.5178),
    "64126": (39.0851, -94.5178),
    "64127": (39.0851, -94.5317),
    "64128": (39.0631, -94.5503),
    "64129": (39.0628, -94.5317),
    "64130": (39.0451, -94.5503),
    "64131": (38.9982, -94.5807),
    "64132": (39.0182, -94.5807),
    "64133": (39.0182, -94.5178),
    "64134": (38.9832, -94.5178),
    "64136": (39.0182, -94.4848),
    "64137": (38.9832, -94.5503),
    "64138": (38.9832, -94.4848),
    "64145": (38.9232, -94.5966),
    "64150": (39.1652, -94.6617),
    "64151": (39.1652, -94.6137),
    "64152": (39.1652, -94.6617),
}


def _haversine_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine distance in miles between two lat/lng points."""
    r = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _cost_tier_order(tier: str) -> int:
    return {"free": 0, "low": 1, "market": 2}.get(tier, 99)


def _has_transit(option: dict) -> bool:
    from backend.data.cache import AppCache
    return option.get("id", "") in AppCache.pantry_transit


@router.get("/options", response_model=OptionsResponse)
def get_options(zip: str = Query(..., description="5-digit KC ZIP code")) -> OptionsResponse:
    zip = zip.strip()

    if not zip.isdigit() or len(zip) != 5 or not zip.startswith(_VALID_ZIP_PREFIX):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ZIP code '{zip}'. Please enter a Kansas City ZIP (641xx).",
        )

    user_center = _ZIP_CENTERS.get(zip)
    need_score = get_score(zip)

    options: list[FoodOption] = []

    for item in AppCache.pantries:
        # Compute distance if we have coordinates
        distance_mi: float | None = None
        item_lat = item.get("lat")
        item_lng = item.get("lng")

        if user_center and item_lat and item_lng:
            distance_mi = round(
                _haversine_miles(user_center[0], user_center[1], item_lat, item_lng), 1
            )
            if distance_mi > _DEFAULT_RADIUS_MI:
                continue  # skip options too far away

        item_type = item.get("type", "pantry")

        # Determine cost tier
        if item_type == "pantry":
            cost_tier = "free"
            est_cost = "$0"
        elif item_type == "delivery":
            cost_tier = item.get("cost_tier", "market")
            est_cost = item.get("est_cost_order", "varies")
        else:
            cost_tier = item.get("cost_tier", "low")
            est_cost = item.get("est_cost_weekly", "varies")

        options.append(
            FoodOption(
                name=item["name"],
                type=item_type,
                cost_tier=cost_tier,
                est_cost=est_cost,
                distance_mi=distance_mi,
                transit_accessible=_has_transit(item),
                languages=item.get("languages", ["en"]),
                id_required=item.get("id_required", False),
                cold_storage=item.get("cold_storage", False),
                hours=item.get("hours", "Call for hours"),
                address=item.get("address") or "Online/Delivery",
            )
        )

    # Sort: cost tier first, then distance
    options.sort(
        key=lambda o: (
            _cost_tier_order(o.cost_tier),
            o.distance_mi if o.distance_mi is not None else 999,
        )
    )

    # Build produce alert
    supply = AppCache.supply_alerts
    produce_alert: ProduceAlert

    if supply.get("active"):
        from backend.ml.produce_routing import top_drop_locations
        drop_locs = top_drop_locations(n=3)
        produce_alert = ProduceAlert(
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
    else:
        produce_alert = ProduceAlert(active=False)

    return OptionsResponse(
        zip=zip,
        need_score=need_score,
        options=options,
        produce_alert=produce_alert,
    )
