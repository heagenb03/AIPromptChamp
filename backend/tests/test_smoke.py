"""Smoke tests — hit every API endpoint and verify basic response shape."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app, raise_server_exceptions=True)


class TestOptionsEndpoint:
    def test_valid_zip_returns_200(self):
        r = client.get("/api/options?zip=64130")
        assert r.status_code == 200, r.text

    def test_response_shape(self):
        r = client.get("/api/options?zip=64130")
        data = r.json()
        assert data["zip"] == "64130"
        assert isinstance(data["need_score"], int)
        assert 0 <= data["need_score"] <= 100
        assert isinstance(data["options"], list)
        assert "produce_alert" in data
        assert isinstance(data["produce_alert"]["active"], bool)

    def test_options_sorted_free_first(self):
        r = client.get("/api/options?zip=64130")
        options = r.json()["options"]
        if len(options) < 2:
            pytest.skip("Not enough options to check sort order")
        tier_order = {"free": 0, "low": 1, "market": 2}
        tiers = [tier_order[o["cost_tier"]] for o in options]
        assert tiers == sorted(tiers), "Options not sorted by cost tier"

    @pytest.mark.parametrize("zip_code", ["64110", "64108", "64114", "64151"])
    def test_primary_kc_zips_return_200(self, zip_code: str):
        r = client.get(f"/api/options?zip={zip_code}")
        assert r.status_code == 200, f"{zip_code}: {r.text}"

    def test_invalid_zip_returns_400(self):
        r = client.get("/api/options?zip=99999")
        assert r.status_code == 400

    def test_non_kc_zip_returns_400(self):
        r = client.get("/api/options?zip=10001")
        assert r.status_code == 400

    def test_empty_zip_returns_400_or_422(self):
        r = client.get("/api/options?zip=")
        assert r.status_code in (400, 422)

    def test_missing_zip_returns_422(self):
        r = client.get("/api/options")
        assert r.status_code == 422

    @pytest.mark.parametrize("zip_code", ["66101", "66105"])
    def test_kck_highest_need_zips_return_200(self, zip_code: str):
        """66101 and 66105 are the top 2 highest-need ZIPs in the data brief."""
        r = client.get(f"/api/options?zip={zip_code}")
        assert r.status_code == 200, f"{zip_code} rejected — KCK ZIPs must be accepted"

    def test_empty_results_returns_list_not_crash(self):
        """ZIP with no nearby pantries should return empty list, not 500."""
        r = client.get("/api/options?zip=64151")
        assert r.status_code == 200
        assert isinstance(r.json()["options"], list)


class TestAlertsEndpoint:
    def test_returns_200(self):
        r = client.get("/api/alerts")
        assert r.status_code == 200, r.text

    def test_response_has_active_field(self):
        data = client.get("/api/alerts").json()
        assert "active" in data
        assert isinstance(data["active"], bool)

    def test_when_active_has_drop_locations(self):
        data = client.get("/api/alerts").json()
        if data["active"]:
            assert isinstance(data["top_drop_locations"], list)
            assert len(data["top_drop_locations"]) > 0
            for loc in data["top_drop_locations"]:
                assert "name" in loc
                assert "routing_score" in loc


class TestVoteEndpoint:
    def test_valid_vote_returns_200(self):
        r = client.post(
            "/api/vote",
            json={"name": "Jane Doe", "zip": "64130", "support": True},
        )
        assert r.status_code == 200, r.text

    def test_response_has_status_and_message(self):
        r = client.post(
            "/api/vote",
            json={"name": "Test User", "zip": "64108", "support": False},
        )
        data = r.json()
        assert data["status"] == "recorded"
        assert isinstance(data["message"], str)

    def test_missing_body_returns_422(self):
        r = client.post("/api/vote")
        assert r.status_code == 422
