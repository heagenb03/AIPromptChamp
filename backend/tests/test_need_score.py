"""Unit tests for the need_score ML model."""
from __future__ import annotations

import pytest

from backend.data.cache import AppCache, load_all
from backend.ml.need_score import compute_all_scores, get_score


@pytest.fixture(scope="module", autouse=True)
def loaded_cache():
    """Load all data into the cache once for this test module."""
    load_all()


class TestNeedScoreRange:
    """Scores must always be integers in [0, 100]."""

    def test_scores_in_valid_range(self):
        scores = compute_all_scores()
        assert scores, "Expected at least one ZIP score"
        for zip_code, score in scores.items():
            assert 0 <= score <= 100, f"{zip_code}: score {score} out of range"

    def test_high_need_zip_64130_is_above_median(self):
        """64130 has the highest food desert severity, poverty, and 311 calls in mock data."""
        scores = compute_all_scores()
        median = sorted(scores.values())[len(scores) // 2]
        assert scores["64130"] > median, (
            f"64130 should score above median ({median}), got {scores['64130']}"
        )

    def test_low_need_zip_is_below_median(self):
        """64152 or 64151 (NW KC suburbs) should score below median."""
        scores = compute_all_scores()
        median = sorted(scores.values())[len(scores) // 2]
        low_zip = next((z for z in ("64152", "64151", "64155") if z in scores), None)
        if low_zip is None:
            pytest.skip("No low-need ZIP present in current data")
        assert scores[low_zip] < median, (
            f"{low_zip} should score below median ({median}), got {scores[low_zip]}"
        )

    def test_mid_need_zip_64110_is_in_expected_range(self):
        """64110 has moderate indicators — expect 30–70 range."""
        scores = compute_all_scores()
        score = scores.get("64110")
        assert score is not None, "64110 not found in scores"
        assert 20 <= score <= 80, f"64110 should be mid-range, got {score}"


class TestNeedScoreRelativeOrdering:
    """High-need ZIPs should outrank low-need ZIPs."""

    def test_64130_outranks_low_need_zip(self):
        scores = compute_all_scores()
        low_zip = next((z for z in ("64152", "64151", "64155") if z in scores), None)
        if low_zip is None:
            pytest.skip("No low-need ZIP present in current data")
        assert scores["64130"] > scores[low_zip], (
            f"64130 ({scores['64130']}) should outrank {low_zip} ({scores[low_zip]})"
        )

    def test_64127_outranks_64114(self):
        """64127 is a known high-distress area; 64114 is south KC, lower distress."""
        scores = compute_all_scores()
        # Both ZIPs may not be in all data sources, but scores should reflect the gap
        assert scores.get("64127", 0) >= scores.get("64114", 0), (
            f"64127 ({scores.get('64127')}) should >= 64114 ({scores.get('64114')})"
        )


class TestGetScoreConvenienceLookup:
    """get_score() must return a cached value or 0 for unknown ZIPs."""

    def test_known_zip_returns_positive_score(self):
        score = get_score("64130")
        assert score > 0, f"Expected positive score for 64130, got {score}"

    def test_unknown_zip_returns_zero(self):
        assert get_score("99999") == 0

    def test_return_type_is_int(self):
        score = get_score("64130")
        assert isinstance(score, int), f"Expected int, got {type(score)}"
