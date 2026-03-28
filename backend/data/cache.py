"""
In-memory cache. All external API data is loaded once at startup.

Usage:
    from backend.data.cache import AppCache
    pantries = AppCache.pantries
    score = AppCache.need_scores.get("64130", 0)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from backend.data.fetcher import (
    fetch_311_calls,
    fetch_demographics,
    fetch_food_atlas,
    fetch_harvest,
    fetch_pantries,
    fetch_store_closures,
    fetch_supply_alerts,
    fetch_transit,
)

logger = logging.getLogger(__name__)


@dataclass
class _Cache:
    pantries: list[dict] = field(default_factory=list)

    # ZIP-keyed dicts for fast lookup
    food_atlas: dict[str, float] = field(default_factory=dict)       # zip → severity
    demographics: dict[str, dict] = field(default_factory=dict)      # zip → {poverty_rate, no_vehicle_pct}
    calls_311: dict[str, int] = field(default_factory=dict)          # zip → call count
    store_closures: dict[str, int] = field(default_factory=dict)     # zip → closure count
    transit: dict[str, dict] = field(default_factory=dict)           # stop_id → stop info

    supply_alerts: dict = field(default_factory=dict)
    harvest: dict = field(default_factory=dict)

    # Computed at startup by ml/need_score.py
    need_scores: dict[str, int] = field(default_factory=dict)        # zip → 0–100


AppCache = _Cache()


def load_all() -> None:
    """Fetch all external data and populate AppCache. Called once at startup."""
    logger.info("Loading all challenge API data into cache...")

    AppCache.pantries = fetch_pantries()
    logger.info("  pantries: %d records", len(AppCache.pantries))

    AppCache.food_atlas = {
        row["zip"]: row["food_desert_severity"]
        for row in fetch_food_atlas()
    }
    logger.info("  food_atlas: %d ZIPs", len(AppCache.food_atlas))

    AppCache.demographics = {
        row["zip"]: {"poverty_rate": row["poverty_rate"], "no_vehicle_pct": row["no_vehicle_pct"]}
        for row in fetch_demographics()
    }
    logger.info("  demographics: %d ZIPs", len(AppCache.demographics))

    AppCache.calls_311 = {
        row["zip"]: row["distress_calls"]
        for row in fetch_311_calls()
    }
    logger.info("  311_calls: %d ZIPs", len(AppCache.calls_311))

    raw_closures: list[dict[str, Any]] = fetch_store_closures()
    AppCache.store_closures = {row["zip"]: row["closures"] for row in raw_closures}
    logger.info("  store_closures: %d ZIPs", len(AppCache.store_closures))

    AppCache.transit = {
        stop["stop_id"]: stop
        for stop in fetch_transit()
    }
    logger.info("  transit: %d stops", len(AppCache.transit))

    AppCache.supply_alerts = fetch_supply_alerts()
    logger.info("  supply_alerts: active=%s", AppCache.supply_alerts.get("active"))

    AppCache.harvest = fetch_harvest()
    logger.info("  harvest: priority_zips=%s", AppCache.harvest.get("priority_zips"))

    # Compute need scores after all data is loaded
    from backend.ml.need_score import compute_all_scores
    AppCache.need_scores = compute_all_scores()
    logger.info("  need_scores computed for %d ZIPs", len(AppCache.need_scores))

    logger.info("Cache load complete.")
