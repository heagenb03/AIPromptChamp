"""
Tests for produce routing curveball — verify routing works with updated
supply-alerts API (1000 lbs, 48 hrs) and that unrecognized alert types
are logged as warnings.
"""
from __future__ import annotations

import logging

import pytest

from backend.data.cache import AppCache, _normalize_supply_alerts


class TestNormalizeSupplyAlerts:
    """_normalize_supply_alerts handles various alert types correctly."""

    def test_produce_donation_type(self) -> None:
        raw = {
            "status": "active",
            "alerts": [
                {
                    "type": "produce_donation",
                    "item": "fresh produce",
                    "pounds": 1000,
                    "expiresInHrs": 48,
                }
            ],
        }
        result = _normalize_supply_alerts(raw)
        assert result["active"] is True
        assert result["pounds"] == 1000
        assert result["expires_in_hrs"] == 48
        assert result["item"] == "fresh produce"

    def test_fresh_produce_type(self) -> None:
        raw = {
            "status": "active",
            "alerts": [
                {
                    "type": "fresh_produce",
                    "item": "lettuce",
                    "pounds": 500,
                    "expiresInHrs": 24,
                }
            ],
        }
        result = _normalize_supply_alerts(raw)
        assert result["active"] is True
        assert result["pounds"] == 500
        assert result["item"] == "lettuce"

    def test_fresh_donation_type(self) -> None:
        raw = {
            "status": "active",
            "alerts": [
                {
                    "type": "fresh_donation",
                    "item": "apples",
                    "pounds": 200,
                    "expires_in_hrs": 12,
                }
            ],
        }
        result = _normalize_supply_alerts(raw)
        assert result["active"] is True
        assert result["pounds"] == 200
        assert result["expires_in_hrs"] == 12

    def test_unrecognized_alert_type_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        raw = {
            "status": "normal",
            "alerts": [
                {"type": "canned_goods_surplus", "item": "beans", "pounds": 300}
            ],
        }
        with caplog.at_level(logging.WARNING, logger="backend.data.cache"):
            result = _normalize_supply_alerts(raw)
        assert any("canned_goods_surplus" in msg for msg in caplog.messages)
        # No produce alert recognized, so active depends on status
        assert result["active"] is False

    def test_no_alerts_list_normal_status(self) -> None:
        raw = {"status": "normal", "alerts": []}
        result = _normalize_supply_alerts(raw)
        assert result["active"] is False

    def test_mock_shape_passthrough(self) -> None:
        raw = {"active": True, "item": "carrots", "pounds": 100, "expires_in_hrs": 6}
        result = _normalize_supply_alerts(raw)
        assert result == raw

    def test_curveball_1000lbs_48hrs(self) -> None:
        """Exact curveball scenario: 1000 lbs, 48 hours."""
        raw = {
            "status": "active",
            "alerts": [
                {
                    "type": "produce_donation",
                    "item": "fresh produce",
                    "pounds": 1000,
                    "expiresInHrs": 48,
                }
            ],
        }
        result = _normalize_supply_alerts(raw)
        assert result["active"] is True
        assert result["pounds"] == 1000
        assert result["expires_in_hrs"] == 48


class TestProduceRoutingIntegration:
    """Integration tests: produce routing works end-to-end via the API."""

    def test_options_endpoint_returns_produce_alert(self) -> None:
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)
        resp = client.get("/api/options?zip=64130")
        assert resp.status_code == 200

        data = resp.json()
        alert = data["produce_alert"]
        assert isinstance(alert["active"], bool)
        # If active, must have drop locations
        if alert["active"]:
            assert len(alert["top_drop_locations"]) > 0
            for loc in alert["top_drop_locations"]:
                assert "name" in loc
                assert "address" in loc
                assert "routing_score" in loc
                assert "reason" in loc

    def test_drop_locations_are_sorted_by_score(self) -> None:
        from backend.ml.produce_routing import top_drop_locations

        locs = top_drop_locations(n=5)
        if len(locs) > 1:
            scores = [loc.routing_score for loc in locs]
            assert scores == sorted(scores, reverse=True)

    def test_top_drop_locations_returns_requested_count(self) -> None:
        from backend.ml.produce_routing import top_drop_locations

        locs = top_drop_locations(n=3)
        assert len(locs) <= 3
