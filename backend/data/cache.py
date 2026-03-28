"""
In-memory cache. All external API data is loaded once at startup.

Field names are normalized to snake_case internally regardless of whether
data comes from the real API (camelCase) or mock data.

Usage:
    from backend.data.cache import AppCache
    pantries = AppCache.pantries
    score = AppCache.need_scores.get("64130", 0)
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field

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

_FREQ_TO_TRIPS_PER_HOUR = {
    "10min": 6,
    "15min": 4,
    "20min": 3,
    "30min": 2,
    "60min": 1,
}


@dataclass
class _Cache:
    pantries: list[dict] = field(default_factory=list)

    # ZIP-keyed dicts for fast lookup
    food_atlas: dict[str, float] = field(default_factory=dict)       # zip → severity (0–1)
    demographics: dict[str, dict] = field(default_factory=dict)      # zip → {poverty_rate, no_vehicle_pct}
    calls_311: dict[str, int] = field(default_factory=dict)          # zip → call count
    store_closures: dict[str, int] = field(default_factory=dict)     # zip → closure count

    # pantry_id → transit info (trips_per_hour, walk_minutes)
    pantry_transit: dict[str, dict] = field(default_factory=dict)

    supply_alerts: dict = field(default_factory=dict)
    harvest_zips: set[str] = field(default_factory=set)              # priority ZIPs

    # Computed at startup by ml/need_score.py
    need_scores: dict[str, int] = field(default_factory=dict)        # zip → 0–100


AppCache = _Cache()


# ---------------------------------------------------------------------------
# Field normalizers — real API uses camelCase; mock uses snake_case
# ---------------------------------------------------------------------------

def _normalize_pantry(p: dict) -> dict:
    """Normalize a pantry record to internal snake_case shape."""
    langs_raw = p.get("language") or p.get("languages") or ["en"]
    languages = [
        "es" if l.lower() in ("spanish", "es") else "en"
        for l in langs_raw
    ]
    raw_type = p.get("type", "pantry")
    _STORE_TYPES = {"store", "grocery", "supermarket"}
    _DELIVERY_TYPES = {"delivery"}
    if raw_type in _STORE_TYPES:
        item_type = "store"
    elif raw_type in _DELIVERY_TYPES:
        item_type = "delivery"
    else:
        item_type = "pantry"  # food_bank, community_garden, shelter_pantry, etc.

    return {
        "id": p.get("id", ""),
        "name": p.get("name", ""),
        "address": p.get("address", ""),
        "zip": p.get("zip", ""),
        "lat": p.get("lat"),
        "lng": p.get("lng"),
        "hours": p.get("hours", ""),
        "languages": languages,
        "id_required": p.get("idRequired") if "idRequired" in p else p.get("id_required", False),
        "cold_storage": p.get("coldStorage") if "coldStorage" in p else p.get("cold_storage", False),
        "type": item_type,
    }


def _normalize_demographics(d: dict) -> tuple[str, dict]:
    """Returns (zip, {poverty_rate, no_vehicle_pct}) — values as fractions 0–1."""
    zip_code = d.get("zip", "")
    # Real API: povertyRate=38.2 (percent), noVehiclePct=38 (percent)
    # Mock: poverty_rate=0.38 (fraction), no_vehicle_pct=0.38 (fraction)
    if "povertyRate" in d:
        poverty = d["povertyRate"] / 100.0
        no_vehicle = d["noVehiclePct"] / 100.0
    else:
        poverty = d.get("poverty_rate", 0.0)
        no_vehicle = d.get("no_vehicle_pct", 0.0)
    return zip_code, {"poverty_rate": poverty, "no_vehicle_pct": no_vehicle}


def _normalize_food_atlas(rows: list[dict]) -> dict[str, float]:
    """
    Aggregate census-tract rows to ZIP level.
    Severity = 1.0 if food desert, 0.5 if low access within 1mi, else 0.0.
    Multiple tracts per ZIP → take max severity.
    """
    per_zip: dict[str, float] = {}
    for row in rows:
        zip_code = row.get("zip", "")
        if not zip_code:
            continue
        if "foodDesert" in row:
            # Real API
            if row.get("foodDesert"):
                severity = 1.0
            elif row.get("lowAccess1mi"):
                severity = 0.5
            else:
                severity = 0.0
        else:
            # Mock: already numeric
            severity = row.get("food_desert_severity", 0.0) / 10.0  # mock is 0–10

        per_zip[zip_code] = max(per_zip.get(zip_code, 0.0), severity)
    return per_zip


def _normalize_311(rows: list[dict]) -> dict[str, int]:
    """ZIP → total distress call count."""
    per_zip: dict[str, int] = {}
    for row in rows:
        zip_code = row.get("zip", "")
        count = row.get("count") if "count" in row else row.get("distress_calls", 0)
        per_zip[zip_code] = per_zip.get(zip_code, 0) + int(count)
    return per_zip


def _normalize_closures(rows: list[dict]) -> dict[str, int]:
    """ZIP → number of store closures."""
    per_zip: dict[str, int] = defaultdict(int)
    for row in rows:
        zip_code = row.get("zip", "")
        # Real API: one row per closure. Mock: one row per ZIP with `closures` count.
        if "closures" in row:
            per_zip[zip_code] += int(row["closures"])
        else:
            per_zip[zip_code] += 1
    return dict(per_zip)


def _normalize_transit(rows: list[dict]) -> dict[str, dict]:
    """
    Returns {pantry_id: {trips_per_hour, walk_minutes}}.
    Real API uses nearPantry; mock uses stop_id (no pantry link — skip for routing).
    """
    result: dict[str, dict] = {}
    for row in rows:
        pantry_id = row.get("nearPantry") or row.get("near_pantry")
        if not pantry_id:
            continue
        freq_str = row.get("frequency", "30min")
        trips = _FREQ_TO_TRIPS_PER_HOUR.get(freq_str, 2)
        result[pantry_id] = {
            "trips_per_hour": trips,
            "walk_minutes": row.get("walkMinutes") or row.get("walk_minutes", 10),
            "route": row.get("route", ""),
        }
    return result


def _normalize_supply_alerts(raw: dict) -> dict:
    """
    Normalise supply-alerts to {active, item, pounds, expires_in_hrs}.
    Checks for a produce/fresh donation type alert.
    """
    # Real API: {status, lastUpdated, alerts: [...]}
    if "alerts" in raw:
        for alert in raw.get("alerts", []):
            if alert.get("type") in ("produce_donation", "fresh_produce", "fresh_donation"):
                return {
                    "active": True,
                    "item": alert.get("item", "fresh produce"),
                    "pounds": alert.get("pounds"),
                    "expires_in_hrs": alert.get("expiresInHrs") or alert.get("expires_in_hrs"),
                }
        # No produce alert active — check status
        return {"active": raw.get("status") not in ("normal", None, "")}

    # Mock shape — already normalized
    return raw


# ---------------------------------------------------------------------------
# Main loader
# ---------------------------------------------------------------------------

def load_all() -> None:
    """Fetch all external data and populate AppCache. Called once at startup."""
    logger.info("Loading all challenge API data into cache...")

    raw_pantries = fetch_pantries()
    AppCache.pantries = [_normalize_pantry(p) for p in raw_pantries]
    logger.info("  pantries: %d records", len(AppCache.pantries))

    AppCache.food_atlas = _normalize_food_atlas(fetch_food_atlas())
    logger.info("  food_atlas: %d ZIPs", len(AppCache.food_atlas))

    AppCache.demographics = {}
    for row in fetch_demographics():
        zip_code, vals = _normalize_demographics(row)
        AppCache.demographics[zip_code] = vals
    logger.info("  demographics: %d ZIPs", len(AppCache.demographics))

    AppCache.calls_311 = _normalize_311(fetch_311_calls())
    logger.info("  311_calls: %d ZIPs", len(AppCache.calls_311))

    AppCache.store_closures = _normalize_closures(fetch_store_closures())
    logger.info("  store_closures: %d ZIPs", len(AppCache.store_closures))

    AppCache.pantry_transit = _normalize_transit(fetch_transit())
    logger.info("  transit: %d pantry links", len(AppCache.pantry_transit))

    AppCache.supply_alerts = _normalize_supply_alerts(fetch_supply_alerts())
    logger.info("  supply_alerts: active=%s", AppCache.supply_alerts.get("active"))

    harvest_rows = fetch_harvest()
    AppCache.harvest_zips = {row["zip"] for row in harvest_rows if "zip" in row}
    logger.info("  harvest: %d priority ZIPs: %s", len(AppCache.harvest_zips), AppCache.harvest_zips)

    # Compute need scores after all data is loaded
    from backend.ml.need_score import compute_all_scores
    AppCache.need_scores = compute_all_scores()
    logger.info("  need_scores computed for %d ZIPs", len(AppCache.need_scores))

    logger.info("Cache load complete.")
