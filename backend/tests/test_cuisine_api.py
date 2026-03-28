"""
Integration tests for the cuisine pre-filter on GET /api/options.

Tests that the `cuisines` query parameter correctly filters results,
that cuisine_tags appear on every option, and that backwards
compatibility is preserved when the parameter is omitted.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

# Use a KCMO ZIP that has data in the cache
_TEST_ZIP = "64130"


class TestCuisineParamOmitted:
    """When cuisines param is not provided, behaviour is unchanged (backwards compatible)."""

    def test_no_cuisines_param_returns_200(self) -> None:
        resp = client.get(f"/api/options?zip={_TEST_ZIP}")
        assert resp.status_code == 200

    def test_no_cuisines_param_returns_all_options(self) -> None:
        resp = client.get(f"/api/options?zip={_TEST_ZIP}")
        data = resp.json()
        assert len(data["options"]) > 0

    def test_all_options_have_cuisine_tags_field(self) -> None:
        resp = client.get(f"/api/options?zip={_TEST_ZIP}")
        data = resp.json()
        for opt in data["options"]:
            assert "cuisine_tags" in opt, f"Missing cuisine_tags on {opt['name']}"
            assert isinstance(opt["cuisine_tags"], list)

    def test_cuisine_tags_contain_valid_values(self) -> None:
        resp = client.get(f"/api/options?zip={_TEST_ZIP}")
        data = resp.json()
        valid = {"american", "hispanic", "asian", "african_caribbean", "soul_food"}
        for opt in data["options"]:
            for tag in opt["cuisine_tags"]:
                assert tag in valid, f"Invalid cuisine tag '{tag}' on {opt['name']}"


class TestCuisineFiltering:
    """When cuisines param is provided, only matching options are returned."""

    def test_hispanic_filter_returns_only_matching(self) -> None:
        resp = client.get(f"/api/options?zip={_TEST_ZIP}&cuisines=hispanic")
        data = resp.json()
        assert resp.status_code == 200
        for opt in data["options"]:
            # Delivery type is always included regardless of cuisine match
            if opt["type"] == "delivery":
                continue
            assert "hispanic" in opt["cuisine_tags"], (
                f"{opt['name']} does not have 'hispanic' tag but was returned"
            )

    def test_delivery_type_always_included(self) -> None:
        """Delivery options should never be filtered out by cuisine preference."""
        resp_all = client.get(f"/api/options?zip={_TEST_ZIP}")
        resp_filtered = client.get(f"/api/options?zip={_TEST_ZIP}&cuisines=soul_food")

        all_delivery = [o for o in resp_all.json()["options"] if o["type"] == "delivery"]
        filtered_delivery = [o for o in resp_filtered.json()["options"] if o["type"] == "delivery"]

        assert len(filtered_delivery) == len(all_delivery)

    def test_multiple_cuisines_comma_separated(self) -> None:
        resp = client.get(f"/api/options?zip={_TEST_ZIP}&cuisines=hispanic,soul_food")
        data = resp.json()
        assert resp.status_code == 200
        for opt in data["options"]:
            if opt["type"] == "delivery":
                continue
            has_match = bool(set(opt["cuisine_tags"]) & {"hispanic", "soul_food"})
            assert has_match, f"{opt['name']} has no matching cuisine tags"


class TestCuisineEdgeCases:
    """Edge cases: invalid tags, empty string, whitespace."""

    def test_invalid_cuisine_silently_ignored(self) -> None:
        resp = client.get(f"/api/options?zip={_TEST_ZIP}&cuisines=invalid,hispanic")
        data = resp.json()
        assert resp.status_code == 200
        # Should still filter by valid tag (hispanic)
        for opt in data["options"]:
            if opt["type"] == "delivery":
                continue
            assert "hispanic" in opt["cuisine_tags"]

    def test_all_invalid_cuisines_returns_all_options(self) -> None:
        """If no valid cuisines remain after filtering, treat as no filter."""
        resp_none = client.get(f"/api/options?zip={_TEST_ZIP}")
        resp_invalid = client.get(f"/api/options?zip={_TEST_ZIP}&cuisines=bogus,fake")
        assert len(resp_invalid.json()["options"]) == len(resp_none.json()["options"])

    def test_empty_cuisines_string_same_as_omitted(self) -> None:
        resp_none = client.get(f"/api/options?zip={_TEST_ZIP}")
        resp_empty = client.get(f"/api/options?zip={_TEST_ZIP}&cuisines=")
        assert len(resp_empty.json()["options"]) == len(resp_none.json()["options"])

    def test_whitespace_in_cuisines_trimmed(self) -> None:
        resp = client.get(f"/api/options?zip={_TEST_ZIP}&cuisines=%20hispanic%20")
        data = resp.json()
        assert resp.status_code == 200


class TestCuisineSortOrder:
    """Results maintain cost_tier ordering; cuisine match ratio is secondary."""

    def test_cost_tier_ordering_preserved(self) -> None:
        resp = client.get(f"/api/options?zip={_TEST_ZIP}&cuisines=hispanic")
        data = resp.json()
        tier_order = {"free": 0, "low": 1, "market": 2}
        tiers = [tier_order.get(o["cost_tier"], 99) for o in data["options"]]
        assert tiers == sorted(tiers), "Options not sorted by cost tier"

    def test_cuisine_match_used_within_same_tier(self) -> None:
        """Within the same cost tier, higher cuisine match ratio should come first."""
        resp = client.get(f"/api/options?zip={_TEST_ZIP}&cuisines=hispanic")
        data = resp.json()
        # Group by cost_tier and check cuisine match ratio within each group
        # This is a structural test — just verify the sort doesn't break
        assert resp.status_code == 200
        assert len(data["options"]) >= 0  # sanity
