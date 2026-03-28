"""Integration tests — verify delivery fields appear in /api/options response."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app, raise_server_exceptions=True)


class TestDeliveryFieldsInOptionsResponse:
    """New additive fields: delivery_options and delivery_necessity_flag."""

    def test_response_contains_delivery_options(self):
        r = client.get("/api/options?zip=64130")
        assert r.status_code == 200
        data = r.json()
        assert "delivery_options" in data, "Missing delivery_options field"
        assert isinstance(data["delivery_options"], list)

    def test_response_contains_delivery_necessity_flag(self):
        r = client.get("/api/options?zip=64130")
        data = r.json()
        assert "delivery_necessity_flag" in data, "Missing delivery_necessity_flag field"
        assert isinstance(data["delivery_necessity_flag"], bool)

    def test_delivery_options_have_required_fields(self):
        r = client.get("/api/options?zip=64130")
        data = r.json()
        required = {
            "name",
            "snap_accepted",
            "ebt_accepted",
            "delivery_fee",
            "order_minimum",
            "estimated_weekly_total",
            "same_day",
            "cost_tier",
            "serves_zip",
            "notes",
        }
        for opt in data["delivery_options"]:
            missing = required - set(opt.keys())
            assert not missing, f"{opt.get('name', '?')} missing: {missing}"

    def test_delivery_options_count_is_five(self):
        r = client.get("/api/options?zip=64130")
        data = r.json()
        assert len(data["delivery_options"]) == 5

    def test_existing_fields_still_present(self):
        """Additive only — existing fields must not be removed."""
        r = client.get("/api/options?zip=64130")
        data = r.json()
        assert "zip" in data
        assert "need_score" in data
        assert "options" in data
        assert "produce_alert" in data

    def test_kc_zip_delivery_serves_zip_true(self):
        r = client.get("/api/options?zip=64130")
        data = r.json()
        for opt in data["delivery_options"]:
            assert opt["serves_zip"] is True

    @pytest.mark.parametrize("zip_code", ["66101", "66105"])
    def test_kck_zip_delivery_serves_zip_true(self, zip_code: str):
        """KCK ZIPs must also get serves_zip=True — they are in the KC metro service area."""
        r = client.get(f"/api/options?zip={zip_code}")
        assert r.status_code == 200, f"{zip_code} rejected"
        data = r.json()
        for opt in data["delivery_options"]:
            assert opt["serves_zip"] is True, (
                f"{zip_code}: {opt['name']} has serves_zip=False"
            )

    @pytest.mark.parametrize("zip_code", ["66101", "66105"])
    def test_kck_zip_has_nonzero_need_score(self, zip_code: str):
        """KCK ZIPs have demographics in mock data — need_score must be > 0."""
        r = client.get(f"/api/options?zip={zip_code}")
        data = r.json()
        assert data["need_score"] > 0, (
            f"{zip_code} need_score is 0 — mock demographics may be missing"
        )
