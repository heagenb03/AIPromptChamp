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


def compute_all_scores() -> dict[str, int]:
    """
    Compute need scores for all ZIPs that have data in the cache.
    Returns a dict of zip_code → score (0–100 integer).
    """
    from backend.data.cache import AppCache

    # Collect all ZIPs that appear in any data source
    all_zips: set[str] = set()
    all_zips.update(AppCache.food_atlas.keys())
    all_zips.update(AppCache.demographics.keys())
    all_zips.update(AppCache.calls_311.keys())
    all_zips.update(AppCache.store_closures.keys())

    if not all_zips:
        logger.warning("No ZIP data in cache — need scores will be empty")
        return {}

    zips = sorted(all_zips)
    n = len(zips)

    # Build feature matrix [n_zips × n_features]
    food_desert = np.array([AppCache.food_atlas.get(z, 0.0) for z in zips])
    poverty = np.array([AppCache.demographics.get(z, {}).get("poverty_rate", 0.0) for z in zips])
    no_vehicle = np.array([AppCache.demographics.get(z, {}).get("no_vehicle_pct", 0.0) for z in zips])
    calls = np.array([float(AppCache.calls_311.get(z, 0)) for z in zips])
    closures = np.array([float(AppCache.store_closures.get(z, 0)) for z in zips])

    # Normalize each feature
    features = {
        "food_desert_severity": _minmax_normalize(food_desert),
        "poverty_rate": _minmax_normalize(poverty),
        "no_vehicle_pct": _minmax_normalize(no_vehicle),
        "distress_calls": _minmax_normalize(calls),
        "store_closures": _minmax_normalize(closures),
    }

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


def get_score(zip_code: str) -> int:
    """Convenience lookup — returns cached score or 0 if ZIP not found."""
    from backend.data.cache import AppCache
    return AppCache.need_scores.get(zip_code, 0)
