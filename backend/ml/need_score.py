"""
Need Score Model — produces a 0–100 urgency score per ZIP code.

Features (all from AppCache, loaded from challenge APIs):
  - food_desert_severity  (weight: 0.30)
  - poverty_rate          (weight: 0.30)
  - no_vehicle_pct        (weight: 0.20)
  - distress_calls_311    (weight: 0.10)
  - store_closures        (weight: 0.10)

Each feature is min-max normalized to [0, 1] across all KC ZIPs, then
a weighted sum is computed and scaled to [0, 100].
"""
from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)

# Feature weights — must sum to 1.0
_WEIGHTS = {
    "food_desert_severity": 0.30,
    "poverty_rate": 0.30,
    "no_vehicle_pct": 0.20,
    "distress_calls": 0.10,
    "store_closures": 0.10,
}


def _minmax_normalize(values: np.ndarray) -> np.ndarray:
    lo, hi = values.min(), values.max()
    if hi == lo:
        return np.zeros_like(values, dtype=float)
    return (values - lo) / (hi - lo)


def _all_data_zips() -> set[str]:
    """Collect all ZIPs that appear in any cache data source."""
    from backend.data.cache import AppCache
    zips: set[str] = set()
    zips.update(AppCache.food_atlas.keys())
    zips.update(AppCache.demographics.keys())
    zips.update(AppCache.calls_311.keys())
    zips.update(AppCache.store_closures.keys())
    return zips


def _build_feature_arrays(zips: list[str]) -> dict[str, np.ndarray]:
    """Build raw (non-normalized) feature arrays for the given ZIPs.

    Returns a dict mapping feature name to a numpy array of raw values,
    one entry per ZIP in the same order as the input list.
    """
    from backend.data.cache import AppCache

    food_desert = np.array([AppCache.food_atlas.get(z, 0.0) for z in zips])
    poverty = np.array([AppCache.demographics.get(z, {}).get("poverty_rate", 0.0) for z in zips])
    no_vehicle = np.array([AppCache.demographics.get(z, {}).get("no_vehicle_pct", 0.0) for z in zips])
    calls = np.array([float(AppCache.calls_311.get(z, 0)) for z in zips])
    closures = np.array([float(AppCache.store_closures.get(z, 0)) for z in zips])

    return {
        "food_desert_severity": food_desert,
        "poverty_rate": poverty,
        "no_vehicle_pct": no_vehicle,
        "distress_calls": calls,
        "store_closures": closures,
    }


def compute_all_scores() -> dict[str, int]:
    """
    Compute need scores for all ZIPs that have data in the cache.
    Returns a dict of zip_code → score (0–100 integer).
    """
    all_zips = _all_data_zips()

    if not all_zips:
        logger.warning("No ZIP data in cache — need scores will be empty")
        return {}

    zips = sorted(all_zips)
    n = len(zips)

    # Build raw feature arrays and normalize
    raw_features = _build_feature_arrays(zips)
    features = {key: _minmax_normalize(arr) for key, arr in raw_features.items()}

    # Weighted sum → scale to [0, 100]
    score = np.zeros(n)
    for feat, weight in _WEIGHTS.items():
        score += weight * features[feat]

    score_int = np.round(score * 100).astype(int)

    result = {zip_code: int(s) for zip_code, s in zip(zips, score_int)}
    logger.info(
        "Need scores: min=%d, max=%d, mean=%.1f",
        min(result.values()),
        max(result.values()),
        sum(result.values()) / len(result),
    )
    return result


def store_score_normalization_params() -> None:
    """Compute and store per-feature min/max into AppCache for breakdown lookups."""
    from backend.data.cache import AppCache

    all_zips = _all_data_zips()

    if not all_zips:
        return

    zips = sorted(all_zips)
    raw = _build_feature_arrays(zips)

    AppCache.score_feature_mins = {key: float(arr.min()) for key, arr in raw.items()}
    AppCache.score_feature_maxes = {key: float(arr.max()) for key, arr in raw.items()}
    logger.info("Stored score normalization params for %d features", len(raw))


def get_score_breakdown(zip_code: str) -> dict[str, float]:
    """Return per-feature normalized values (0-1, rounded to 2dp) for a ZIP.

    Returns all zeros if normalization params have not been stored yet.
    """
    from backend.data.cache import AppCache

    feature_keys = list(_WEIGHTS.keys())

    if not AppCache.score_feature_mins:
        return {key: 0.0 for key in feature_keys}

    raw = _build_feature_arrays([zip_code])
    result: dict[str, float] = {}

    for key in feature_keys:
        lo = AppCache.score_feature_mins.get(key, 0.0)
        hi = AppCache.score_feature_maxes.get(key, 0.0)
        raw_val = float(raw[key][0])

        if hi == lo:
            normalized = 0.0
        else:
            normalized = (raw_val - lo) / (hi - lo)

        # Clamp to [0, 1] and round
        normalized = round(max(0.0, min(1.0, normalized)), 2)
        result[key] = normalized

    return result


def get_score(zip_code: str) -> int:
    """Convenience lookup — returns cached score or 0 if ZIP not found."""
    from backend.data.cache import AppCache
    return AppCache.need_scores.get(zip_code, 0)


def compute_delivery_necessity(no_vehicle_pct: float, transit_pantry_count: int) -> bool:
    """
    Determine if delivery services are a necessity for a given area.

    Rule: (no_vehicle_pct > 0.35) AND (transit_accessible_pantry_count < 2)
    """
    return no_vehicle_pct > 0.35 and transit_pantry_count < 2


def get_delivery_necessity_for_zip(zip_code: str) -> bool:
    """
    Look up demographics and transit data from cache, then compute
    whether delivery is a necessity for the given ZIP.
    """
    from backend.data.cache import AppCache

    demo = AppCache.demographics.get(zip_code)
    if demo is None:
        return False

    no_vehicle_pct: float = demo.get("no_vehicle_pct", 0.0)

    # Count pantries in this ZIP that have a transit link
    transit_pantry_count = 0
    for pantry in AppCache.pantries:
        if pantry.get("zip") == zip_code:
            pantry_id = pantry.get("id", "")
            if pantry_id in AppCache.pantry_transit:
                transit_pantry_count += 1

    return compute_delivery_necessity(no_vehicle_pct, transit_pantry_count)
