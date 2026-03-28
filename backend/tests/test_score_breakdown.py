"""Unit + integration tests for Phase 2A: Need Score Breakdown."""
from __future__ import annotations

import pytest
import numpy as np


class TestBuildFeatureArrays:
    """_build_feature_arrays extracts raw (non-normalized) feature arrays from cache."""

    def test_returns_dict_with_all_feature_keys(self):
        from backend.ml.need_score import _build_feature_arrays
        from backend.data.cache import AppCache

        zips = sorted(
            set(AppCache.food_atlas.keys())
            | set(AppCache.demographics.keys())
        )
        if not zips:
            pytest.skip("No ZIPs in cache")

        result = _build_feature_arrays(zips)

        expected_keys = {
            "food_desert_severity",
            "poverty_rate",
            "no_vehicle_pct",
            "distress_calls",
            "store_closures",
        }
        assert set(result.keys()) == expected_keys

    def test_arrays_have_correct_length(self):
        from backend.ml.need_score import _build_feature_arrays
        from backend.data.cache import AppCache

        zips = sorted(
            set(AppCache.food_atlas.keys())
            | set(AppCache.demographics.keys())
        )
        if not zips:
            pytest.skip("No ZIPs in cache")

        result = _build_feature_arrays(zips)
        for key, arr in result.items():
            assert len(arr) == len(zips), f"{key} has wrong length"

    def test_returns_numpy_arrays(self):
        from backend.ml.need_score import _build_feature_arrays

        result = _build_feature_arrays(["64130"])
        for key, arr in result.items():
            assert isinstance(arr, np.ndarray), f"{key} is not ndarray"

    def test_empty_zips_returns_empty_arrays(self):
        from backend.ml.need_score import _build_feature_arrays

        result = _build_feature_arrays([])
        for key, arr in result.items():
            assert len(arr) == 0

    def test_missing_zip_defaults_to_zero(self):
        from backend.ml.need_score import _build_feature_arrays

        result = _build_feature_arrays(["99999"])
        for key, arr in result.items():
            assert arr[0] == 0.0, f"{key} should default to 0.0 for unknown ZIP"


class TestStoreScoreNormalizationParams:
    """store_score_normalization_params populates AppCache min/max dicts."""

    def test_populates_score_feature_mins(self):
        from backend.ml.need_score import store_score_normalization_params
        from backend.data.cache import AppCache

        store_score_normalization_params()

        assert isinstance(AppCache.score_feature_mins, dict)
        assert len(AppCache.score_feature_mins) == 5

    def test_populates_score_feature_maxes(self):
        from backend.ml.need_score import store_score_normalization_params
        from backend.data.cache import AppCache

        store_score_normalization_params()

        assert isinstance(AppCache.score_feature_maxes, dict)
        assert len(AppCache.score_feature_maxes) == 5

    def test_mins_less_than_or_equal_maxes(self):
        from backend.ml.need_score import store_score_normalization_params
        from backend.data.cache import AppCache

        store_score_normalization_params()

        for key in AppCache.score_feature_mins:
            assert AppCache.score_feature_mins[key] <= AppCache.score_feature_maxes[key], (
                f"{key}: min ({AppCache.score_feature_mins[key]}) > max ({AppCache.score_feature_maxes[key]})"
            )

    def test_all_feature_keys_present(self):
        from backend.ml.need_score import store_score_normalization_params
        from backend.data.cache import AppCache

        store_score_normalization_params()

        expected_keys = {
            "food_desert_severity",
            "poverty_rate",
            "no_vehicle_pct",
            "distress_calls",
            "store_closures",
        }
        assert set(AppCache.score_feature_mins.keys()) == expected_keys
        assert set(AppCache.score_feature_maxes.keys()) == expected_keys


class TestGetScoreBreakdown:
    """get_score_breakdown returns per-feature normalized values for a ZIP."""

    def test_returns_dict_with_all_features(self):
        from backend.ml.need_score import (
            get_score_breakdown,
            store_score_normalization_params,
        )

        store_score_normalization_params()
        result = get_score_breakdown("64130")

        expected_keys = {
            "food_desert_severity",
            "poverty_rate",
            "no_vehicle_pct",
            "distress_calls",
            "store_closures",
        }
        assert set(result.keys()) == expected_keys

    def test_values_clamped_between_zero_and_one(self):
        from backend.ml.need_score import (
            get_score_breakdown,
            store_score_normalization_params,
        )

        store_score_normalization_params()
        result = get_score_breakdown("64130")

        for key, val in result.items():
            assert 0.0 <= val <= 1.0, f"{key}={val} outside [0,1]"

    def test_values_rounded_to_two_decimals(self):
        from backend.ml.need_score import (
            get_score_breakdown,
            store_score_normalization_params,
        )

        store_score_normalization_params()
        result = get_score_breakdown("64130")

        for key, val in result.items():
            assert val == round(val, 2), f"{key}={val} not rounded to 2 decimals"

    def test_unknown_zip_returns_all_zeros(self):
        from backend.ml.need_score import (
            get_score_breakdown,
            store_score_normalization_params,
        )

        store_score_normalization_params()
        result = get_score_breakdown("99999")

        for key, val in result.items():
            assert val == 0.0, f"{key} should be 0.0 for unknown ZIP, got {val}"

    def test_returns_all_zeros_when_no_normalization_params(self):
        from backend.ml.need_score import get_score_breakdown
        from backend.data.cache import AppCache

        # Temporarily clear normalization params
        saved_mins = AppCache.score_feature_mins
        saved_maxes = AppCache.score_feature_maxes
        try:
            AppCache.score_feature_mins = {}
            AppCache.score_feature_maxes = {}

            result = get_score_breakdown("64130")

            for key, val in result.items():
                assert val == 0.0, f"{key} should be 0.0 when no normalization params"
        finally:
            AppCache.score_feature_mins = saved_mins
            AppCache.score_feature_maxes = saved_maxes


class TestCacheHasNormalizationFields:
    """_Cache dataclass has score_feature_mins and score_feature_maxes fields."""

    def test_cache_has_score_feature_mins(self):
        from backend.data.cache import AppCache

        assert hasattr(AppCache, "score_feature_mins")
        assert isinstance(AppCache.score_feature_mins, dict)

    def test_cache_has_score_feature_maxes(self):
        from backend.data.cache import AppCache

        assert hasattr(AppCache, "score_feature_maxes")
        assert isinstance(AppCache.score_feature_maxes, dict)


class TestOptionsResponseHasBreakdown:
    """OptionsResponse schema includes need_score_breakdown field."""

    def test_schema_has_need_score_breakdown(self):
        from backend.models.schemas import OptionsResponse

        fields = OptionsResponse.model_fields
        assert "need_score_breakdown" in fields

    def test_need_score_breakdown_defaults_to_empty_dict(self):
        from backend.models.schemas import OptionsResponse, ProduceAlert

        resp = OptionsResponse(
            zip="64130",
            need_score=50,
            options=[],
            produce_alert=ProduceAlert(active=False),
        )
        assert resp.need_score_breakdown == {}

    def test_need_score_breakdown_accepts_feature_dict(self):
        from backend.models.schemas import OptionsResponse, ProduceAlert

        breakdown = {
            "food_desert_severity": 0.75,
            "poverty_rate": 0.50,
            "no_vehicle_pct": 0.30,
            "distress_calls": 0.10,
            "store_closures": 0.05,
        }
        resp = OptionsResponse(
            zip="64130",
            need_score=50,
            options=[],
            produce_alert=ProduceAlert(active=False),
            need_score_breakdown=breakdown,
        )
        assert resp.need_score_breakdown == breakdown


class TestApiReturnsBreakdown:
    """GET /api/options includes need_score_breakdown in response."""

    def test_response_contains_need_score_breakdown(self):
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)
        resp = client.get("/api/options?zip=64130")
        assert resp.status_code == 200

        data = resp.json()
        assert "need_score_breakdown" in data
        assert isinstance(data["need_score_breakdown"], dict)

    def test_breakdown_has_all_five_features(self):
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)
        resp = client.get("/api/options?zip=64130")
        data = resp.json()

        expected_keys = {
            "food_desert_severity",
            "poverty_rate",
            "no_vehicle_pct",
            "distress_calls",
            "store_closures",
        }
        assert set(data["need_score_breakdown"].keys()) == expected_keys

    def test_breakdown_values_are_floats_between_0_and_1(self):
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)
        resp = client.get("/api/options?zip=64130")
        data = resp.json()

        for key, val in data["need_score_breakdown"].items():
            assert isinstance(val, (int, float)), f"{key} is not numeric"
            assert 0.0 <= val <= 1.0, f"{key}={val} outside [0,1]"


class TestComputeAllScoresRefactored:
    """compute_all_scores still works correctly after refactoring to use _build_feature_arrays."""

    def test_returns_nonempty_dict(self):
        from backend.ml.need_score import compute_all_scores

        scores = compute_all_scores()
        assert len(scores) > 0

    def test_scores_in_valid_range(self):
        from backend.ml.need_score import compute_all_scores

        scores = compute_all_scores()
        for zip_code, score in scores.items():
            assert 0 <= score <= 100, f"{zip_code} score {score} out of range"

    def test_known_zip_has_score(self):
        from backend.ml.need_score import compute_all_scores

        scores = compute_all_scores()
        # At least one KC ZIP should have a score
        kc_zips = [z for z in scores if z.startswith("641") or z.startswith("661")]
        assert len(kc_zips) > 0
