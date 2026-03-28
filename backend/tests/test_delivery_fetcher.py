"""Unit tests for delivery_fetcher — static KC delivery providers."""
from __future__ import annotations

import pytest


class TestGetStaticDeliveryProviders:
    """get_static_delivery_providers() must return the 5 hardcoded KC providers."""

    def test_returns_five_providers(self):
        from backend.data.delivery_fetcher import get_static_delivery_providers

        providers = get_static_delivery_providers()
        assert len(providers) == 5

    def test_all_required_fields_present(self):
        from backend.data.delivery_fetcher import get_static_delivery_providers

        required = {
            "name",
            "snap_accepted",
            "ebt_accepted",
            "delivery_fee",
            "order_minimum",
            "estimated_weekly_total",
            "same_day",
            "cost_tier",
            "notes",
        }
        for provider in get_static_delivery_providers():
            missing = required - set(provider.keys())
            assert not missing, f"{provider['name']} missing fields: {missing}"

    def test_estimated_weekly_total_equals_min_plus_fee(self):
        from backend.data.delivery_fetcher import get_static_delivery_providers

        for p in get_static_delivery_providers():
            expected = round(p["order_minimum"] + p["delivery_fee"], 2)
            assert p["estimated_weekly_total"] == expected, (
                f"{p['name']}: expected {expected}, got {p['estimated_weekly_total']}"
            )

    def test_cost_tier_is_valid(self):
        from backend.data.delivery_fetcher import get_static_delivery_providers

        valid_tiers = {"free", "low", "market"}
        for p in get_static_delivery_providers():
            assert p["cost_tier"] in valid_tiers, (
                f"{p['name']} has invalid cost_tier: {p['cost_tier']}"
            )

    def test_snap_and_ebt_are_bools(self):
        from backend.data.delivery_fetcher import get_static_delivery_providers

        for p in get_static_delivery_providers():
            assert isinstance(p["snap_accepted"], bool), f"{p['name']} snap_accepted not bool"
            assert isinstance(p["ebt_accepted"], bool), f"{p['name']} ebt_accepted not bool"

    def test_delivery_fee_and_minimum_are_positive(self):
        from backend.data.delivery_fetcher import get_static_delivery_providers

        for p in get_static_delivery_providers():
            assert p["delivery_fee"] > 0, f"{p['name']} delivery_fee <= 0"
            assert p["order_minimum"] > 0, f"{p['name']} order_minimum <= 0"

    def test_known_provider_names(self):
        from backend.data.delivery_fetcher import get_static_delivery_providers

        names = {p["name"] for p in get_static_delivery_providers()}
        expected_names = {
            "Walmart Grocery",
            "Amazon Fresh",
            "Instacart (Aldi/Price Chopper)",
            "Dillons/Kroger",
            "Hy-Vee Aisles Online",
        }
        assert names == expected_names

    def test_walmart_snap_and_ebt(self):
        from backend.data.delivery_fetcher import get_static_delivery_providers

        walmart = next(p for p in get_static_delivery_providers() if p["name"] == "Walmart Grocery")
        assert walmart["snap_accepted"] is True
        assert walmart["ebt_accepted"] is True
        assert walmart["delivery_fee"] == 7.95
        assert walmart["order_minimum"] == 35.00
        assert walmart["cost_tier"] == "low"

    def test_hyvee_no_snap_no_ebt(self):
        from backend.data.delivery_fetcher import get_static_delivery_providers

        hyvee = next(p for p in get_static_delivery_providers() if p["name"] == "Hy-Vee Aisles Online")
        assert hyvee["snap_accepted"] is False
        assert hyvee["ebt_accepted"] is False


class TestFilterProvidersByZip:
    """filter_providers_by_zip marks serves_zip based on KC ZIP prefix."""

    def test_kc_zip_marks_serves_zip_true(self):
        from backend.data.delivery_fetcher import filter_providers_by_zip

        results = filter_providers_by_zip("64130")
        assert all(p["serves_zip"] is True for p in results)

    def test_kck_zip_marks_serves_zip_true(self):
        """66101 and 66105 are KCK (Kansas City, Kansas) — must be served."""
        from backend.data.delivery_fetcher import filter_providers_by_zip

        for zip_code in ("66101", "66105"):
            results = filter_providers_by_zip(zip_code)
            assert all(p["serves_zip"] is True for p in results), (
                f"{zip_code} should have serves_zip=True"
            )

    def test_non_kc_zip_marks_serves_zip_false(self):
        from backend.data.delivery_fetcher import filter_providers_by_zip

        results = filter_providers_by_zip("10001")
        assert all(p["serves_zip"] is False for p in results)

    def test_preserves_all_original_fields(self):
        from backend.data.delivery_fetcher import filter_providers_by_zip

        results = filter_providers_by_zip("64130")
        assert len(results) == 5
        for p in results:
            assert "name" in p
            assert "serves_zip" in p


class TestSubsidyVisualizationFields:
    """Phase 2B: delivery providers include subsidy breakdown fields."""

    def test_all_providers_have_subsidy_fields(self):
        from backend.data.delivery_fetcher import get_static_delivery_providers

        required = {"market_rate", "subsidy_applied", "final_cost", "subsidy_label"}
        for p in get_static_delivery_providers():
            missing = required - set(p.keys())
            assert not missing, f"{p['name']} missing subsidy fields: {missing}"

    def test_snap_ebt_provider_has_subsidy_applied(self):
        """Walmart accepts SNAP+EBT, so subsidy_applied should equal delivery_fee."""
        from backend.data.delivery_fetcher import get_static_delivery_providers

        walmart = next(
            p for p in get_static_delivery_providers() if p["name"] == "Walmart Grocery"
        )
        assert walmart["snap_accepted"] is True
        assert walmart["subsidy_applied"] == walmart["delivery_fee"]
        assert walmart["final_cost"] == walmart["order_minimum"]
        assert walmart["market_rate"] == round(
            walmart["delivery_fee"] + walmart["order_minimum"], 2
        )
        assert walmart["subsidy_label"] is not None

    def test_non_snap_provider_has_zero_subsidy(self):
        """Hy-Vee has no SNAP/EBT, so subsidy_applied should be 0."""
        from backend.data.delivery_fetcher import get_static_delivery_providers

        hyvee = next(
            p for p in get_static_delivery_providers()
            if p["name"] == "Hy-Vee Aisles Online"
        )
        assert hyvee["snap_accepted"] is False
        assert hyvee["ebt_accepted"] is False
        assert hyvee["subsidy_applied"] == 0.0
        assert hyvee["final_cost"] == round(
            hyvee["delivery_fee"] + hyvee["order_minimum"], 2
        )
        assert hyvee["subsidy_label"] is None

    def test_market_rate_equals_fee_plus_minimum(self):
        """market_rate should always be delivery_fee + order_minimum."""
        from backend.data.delivery_fetcher import get_static_delivery_providers

        for p in get_static_delivery_providers():
            expected = round(p["delivery_fee"] + p["order_minimum"], 2)
            assert p["market_rate"] == expected, (
                f"{p['name']}: market_rate {p['market_rate']} != {expected}"
            )

    def test_final_cost_plus_subsidy_equals_market_rate(self):
        """final_cost + subsidy_applied should equal market_rate."""
        from backend.data.delivery_fetcher import get_static_delivery_providers

        for p in get_static_delivery_providers():
            assert round(p["final_cost"] + p["subsidy_applied"], 2) == p["market_rate"], (
                f"{p['name']}: final_cost + subsidy != market_rate"
            )

    def test_instacart_snap_only_has_subsidy(self):
        """Instacart accepts SNAP but not EBT — should still get subsidy."""
        from backend.data.delivery_fetcher import get_static_delivery_providers

        instacart = next(
            p for p in get_static_delivery_providers()
            if p["name"] == "Instacart (Aldi/Price Chopper)"
        )
        assert instacart["snap_accepted"] is True
        assert instacart["ebt_accepted"] is False
        assert instacart["subsidy_applied"] > 0
        assert instacart["subsidy_label"] is not None


class TestDeliveryOptionSchemaSubsidyFields:
    """DeliveryOption Pydantic model includes subsidy fields."""

    def test_schema_has_subsidy_fields(self):
        from backend.models.schemas import DeliveryOption

        fields = DeliveryOption.model_fields
        assert "market_rate" in fields
        assert "subsidy_applied" in fields
        assert "final_cost" in fields
        assert "subsidy_label" in fields

    def test_subsidy_fields_default_to_none(self):
        from backend.models.schemas import DeliveryOption

        opt = DeliveryOption(
            name="Test",
            snap_accepted=False,
            ebt_accepted=False,
            delivery_fee=5.0,
            order_minimum=10.0,
            estimated_weekly_total=15.0,
            same_day=True,
            cost_tier="low",
            serves_zip=True,
            notes="test",
        )
        assert opt.market_rate is None
        assert opt.subsidy_applied is None
        assert opt.final_cost is None
        assert opt.subsidy_label is None

    def test_subsidy_fields_accept_values(self):
        from backend.models.schemas import DeliveryOption

        opt = DeliveryOption(
            name="Test",
            snap_accepted=True,
            ebt_accepted=True,
            delivery_fee=5.0,
            order_minimum=10.0,
            estimated_weekly_total=15.0,
            same_day=True,
            cost_tier="low",
            serves_zip=True,
            notes="test",
            market_rate=15.0,
            subsidy_applied=5.0,
            final_cost=10.0,
            subsidy_label="SNAP/EBT discount applied",
        )
        assert opt.market_rate == 15.0
        assert opt.subsidy_applied == 5.0
        assert opt.final_cost == 10.0
        assert opt.subsidy_label == "SNAP/EBT discount applied"


class TestApiReturnsSubsidyFields:
    """GET /api/options delivery_options include subsidy fields."""

    def test_delivery_options_have_subsidy_fields(self):
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)
        resp = client.get("/api/options?zip=64130")
        assert resp.status_code == 200

        data = resp.json()
        for opt in data.get("delivery_options", []):
            assert "market_rate" in opt
            assert "subsidy_applied" in opt
            assert "final_cost" in opt
            assert "subsidy_label" in opt
