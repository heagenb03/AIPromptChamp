"""Unit tests for delivery necessity computation."""
from __future__ import annotations

from unittest.mock import patch

import pytest


class TestComputeDeliveryNecessity:
    """
    Rule: delivery_necessity = (no_vehicle_pct > 0.35) AND (transit_accessible_pantry_count < 2)
    """

    def test_high_no_vehicle_zero_transit_pantries_returns_true(self):
        from backend.ml.need_score import compute_delivery_necessity

        # no_vehicle_pct=0.48, transit_pantry_count=0 => True
        assert compute_delivery_necessity(0.48, 0) is True

    def test_high_no_vehicle_one_transit_pantry_returns_true(self):
        from backend.ml.need_score import compute_delivery_necessity

        # no_vehicle_pct=0.50, transit_pantry_count=1 => True
        assert compute_delivery_necessity(0.50, 1) is True

    def test_high_no_vehicle_two_transit_pantries_returns_false(self):
        from backend.ml.need_score import compute_delivery_necessity

        # no_vehicle_pct=0.48, transit_pantry_count=2 => False (>= 2 pantries)
        assert compute_delivery_necessity(0.48, 2) is False

    def test_low_no_vehicle_zero_transit_pantries_returns_false(self):
        from backend.ml.need_score import compute_delivery_necessity

        # no_vehicle_pct=0.10, transit_pantry_count=0 => False (low no_vehicle)
        assert compute_delivery_necessity(0.10, 0) is False

    def test_boundary_no_vehicle_exactly_035_returns_false(self):
        from backend.ml.need_score import compute_delivery_necessity

        # Exactly at threshold (0.35) should be False — condition is strictly greater than
        assert compute_delivery_necessity(0.35, 0) is False

    def test_boundary_no_vehicle_just_above_035(self):
        from backend.ml.need_score import compute_delivery_necessity

        assert compute_delivery_necessity(0.351, 0) is True

    def test_low_no_vehicle_many_pantries_returns_false(self):
        from backend.ml.need_score import compute_delivery_necessity

        assert compute_delivery_necessity(0.05, 10) is False


class TestGetDeliveryNecessityForZip:
    """
    get_delivery_necessity_for_zip(zip_code) should look up demographics
    and transit data from the cache and return a bool.
    """

    def test_high_need_zip_returns_true(self):
        from backend.data.cache import AppCache
        from backend.ml.need_score import get_delivery_necessity_for_zip

        # Mock cache with high no-vehicle pct and no transit-accessible pantries
        original_demographics = AppCache.demographics.copy()
        original_pantries = list(AppCache.pantries)
        original_transit = dict(AppCache.pantry_transit)

        try:
            AppCache.demographics["64999"] = {
                "poverty_rate": 0.40,
                "no_vehicle_pct": 0.48,
            }
            # No pantries in this ZIP, no transit links
            AppCache.pantries = [
                {"id": "p1", "name": "Far Pantry", "zip": "64000", "address": "123 St"},
            ]
            AppCache.pantry_transit = {}  # no transit-accessible pantries

            result = get_delivery_necessity_for_zip("64999")
            assert result is True
        finally:
            AppCache.demographics = original_demographics
            AppCache.pantries = original_pantries
            AppCache.pantry_transit = original_transit

    def test_low_need_zip_returns_false(self):
        from backend.data.cache import AppCache
        from backend.ml.need_score import get_delivery_necessity_for_zip

        original_demographics = AppCache.demographics.copy()
        original_pantries = list(AppCache.pantries)
        original_transit = dict(AppCache.pantry_transit)

        try:
            AppCache.demographics["64998"] = {
                "poverty_rate": 0.10,
                "no_vehicle_pct": 0.05,
            }
            AppCache.pantries = [
                {"id": "p1", "name": "Pantry A", "zip": "64998", "address": "1 St"},
                {"id": "p2", "name": "Pantry B", "zip": "64998", "address": "2 St"},
                {"id": "p3", "name": "Pantry C", "zip": "64998", "address": "3 St"},
            ]
            AppCache.pantry_transit = {"p1": {}, "p2": {}, "p3": {}}

            result = get_delivery_necessity_for_zip("64998")
            assert result is False
        finally:
            AppCache.demographics = original_demographics
            AppCache.pantries = original_pantries
            AppCache.pantry_transit = original_transit

    def test_unknown_zip_returns_false(self):
        from backend.ml.need_score import get_delivery_necessity_for_zip

        # ZIP with no demographics data should default to False
        result = get_delivery_necessity_for_zip("00000")
        assert result is False
