"""
Produce Routing — curveball logic.

When a fresh produce donation is detected, scores all pantries and returns
the top 3 recommended drop locations.

Routing formula (per spec):
  score = 0.4 * need_score(zip)
        + 0.3 * has_cold_storage
        + 0.2 * transit_frequency(nearest_bus_stop)   [normalized 0–1]
        + 0.1 * language_match(es)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_MAX_TRANSIT_FREQ = 6.0  # trips/hour cap for normalization


@dataclass
class DropLocation:
    name: str
    address: str
    routing_score: float
    reason: str


def _transit_score(pantry: dict) -> float:
    """Trips/hour for nearest bus stop to this pantry, normalized 0–1."""
    from backend.data.cache import AppCache

    pantry_id: str = pantry.get("id", "")
    transit = AppCache.pantry_transit.get(pantry_id, {})
    trips = transit.get("trips_per_hour", 0)
    return min(trips / _MAX_TRANSIT_FREQ, 1.0)


def _build_reason(need_score_raw: float, cold_storage: bool, transit: float, lang_es: bool) -> str:
    parts: list[str] = []
    if need_score_raw >= 0.7:
        parts.append("high-need ZIP")
    elif need_score_raw >= 0.4:
        parts.append("moderate-need ZIP")
    if cold_storage:
        parts.append("cold storage available")
    if transit >= 0.5:
        parts.append("frequent transit access")
    elif transit > 0:
        parts.append("transit accessible")
    if lang_es:
        parts.append("Spanish-speaking community")
    return ", ".join(parts).capitalize() if parts else "Available pantry"


def top_drop_locations(n: int = 3) -> list[DropLocation]:
    """Score all pantries and return the top-n recommended drop locations."""
    from backend.data.cache import AppCache
    from backend.ml.need_score import get_score

    pantries = [p for p in AppCache.pantries if p.get("type") not in ("store", "delivery")]
    if not pantries:
        logger.warning("No pantries in cache for produce routing")
        return []

    scored: list[tuple[float, DropLocation]] = []

    for pantry in pantries:
        zip_code: str = pantry.get("zip", "")
        raw_score = get_score(zip_code) / 100.0  # normalize 0–1

        cold = 1.0 if pantry.get("cold_storage", False) else 0.0
        transit = _transit_score(pantry)
        lang_es = 1.0 if "es" in pantry.get("languages", []) else 0.0

        composite = (
            0.4 * raw_score
            + 0.3 * cold
            + 0.2 * transit
            + 0.1 * lang_es
        )

        reason = _build_reason(raw_score, bool(cold), transit, bool(lang_es))
        loc = DropLocation(
            name=pantry["name"],
            address=pantry.get("address", ""),
            routing_score=round(composite * 100, 1),
            reason=reason,
        )
        scored.append((composite, loc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [loc for _, loc in scored[:n]]
