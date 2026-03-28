"""
Unit tests for backend.data.cuisine_tags module.

Tests the cuisine tagging system: static map lookups, heuristic inference,
and the enrichment function that combines both.
"""
from __future__ import annotations

import pytest


class TestValidCuisines:
    """VALID_CUISINES constant has exactly the 5 expected cuisine keys."""

    def test_valid_cuisines_has_five_values(self) -> None:
        from backend.data.cuisine_tags import VALID_CUISINES

        assert len(VALID_CUISINES) == 5

    def test_valid_cuisines_contains_expected_keys(self) -> None:
        from backend.data.cuisine_tags import VALID_CUISINES

        expected = {"american", "hispanic", "asian", "african_caribbean", "soul_food"}
        assert VALID_CUISINES == expected

    def test_valid_cuisines_is_frozenset(self) -> None:
        from backend.data.cuisine_tags import VALID_CUISINES

        assert isinstance(VALID_CUISINES, frozenset)


class TestInferCuisineTags:
    """Heuristic inference for pantries not in the static map."""

    def test_english_only_pantry_returns_only_american(self) -> None:
        from backend.data.cuisine_tags import infer_cuisine_tags

        pantry = {"name": "Generic Pantry", "languages": ["en"], "type": "pantry"}
        tags = infer_cuisine_tags(pantry)
        assert tags == ["american"]

    def test_es_language_adds_hispanic(self) -> None:
        from backend.data.cuisine_tags import infer_cuisine_tags

        pantry = {"name": "Some Pantry", "languages": ["en", "es"], "type": "pantry"}
        tags = infer_cuisine_tags(pantry)
        assert "american" in tags
        assert "hispanic" in tags

    def test_name_guadalupe_adds_hispanic(self) -> None:
        from backend.data.cuisine_tags import infer_cuisine_tags

        pantry = {"name": "Guadalupe Centers", "languages": ["en"], "type": "pantry"}
        tags = infer_cuisine_tags(pantry)
        assert "hispanic" in tags

    def test_name_chavez_adds_hispanic(self) -> None:
        from backend.data.cuisine_tags import infer_cuisine_tags

        pantry = {"name": "Cesar E Chavez Community", "languages": ["en"], "type": "pantry"}
        tags = infer_cuisine_tags(pantry)
        assert "hispanic" in tags

    def test_name_hispanic_keyword_case_insensitive(self) -> None:
        from backend.data.cuisine_tags import infer_cuisine_tags

        pantry = {"name": "HISPANIC Heritage Pantry", "languages": ["en"], "type": "pantry"}
        tags = infer_cuisine_tags(pantry)
        assert "hispanic" in tags

    def test_name_latino_adds_hispanic(self) -> None:
        from backend.data.cuisine_tags import infer_cuisine_tags

        pantry = {"name": "Latino Center Food Bank", "languages": ["en"], "type": "pantry"}
        tags = infer_cuisine_tags(pantry)
        assert "hispanic" in tags

    def test_name_mexican_adds_hispanic(self) -> None:
        from backend.data.cuisine_tags import infer_cuisine_tags

        pantry = {"name": "Mexican American Council", "languages": ["en"], "type": "pantry"}
        tags = infer_cuisine_tags(pantry)
        assert "hispanic" in tags

    def test_store_type_returns_all_five_cuisines(self) -> None:
        from backend.data.cuisine_tags import infer_cuisine_tags

        pantry = {"name": "Price Chopper", "languages": ["en"], "type": "store"}
        tags = infer_cuisine_tags(pantry)
        assert set(tags) == {"american", "hispanic", "asian", "african_caribbean", "soul_food"}

    def test_delivery_type_returns_all_five_cuisines(self) -> None:
        from backend.data.cuisine_tags import infer_cuisine_tags

        pantry = {"name": "Walmart Delivery", "languages": ["en"], "type": "delivery"}
        tags = infer_cuisine_tags(pantry)
        assert set(tags) == {"american", "hispanic", "asian", "african_caribbean", "soul_food"}

    def test_no_languages_key_defaults_to_american_only(self) -> None:
        from backend.data.cuisine_tags import infer_cuisine_tags

        pantry = {"name": "Basic Pantry", "type": "pantry"}
        tags = infer_cuisine_tags(pantry)
        assert tags == ["american"]

    def test_empty_languages_list_defaults_to_american_only(self) -> None:
        from backend.data.cuisine_tags import infer_cuisine_tags

        pantry = {"name": "Basic Pantry", "languages": [], "type": "pantry"}
        tags = infer_cuisine_tags(pantry)
        assert tags == ["american"]

    def test_no_duplicate_tags(self) -> None:
        """A pantry with es language AND 'Guadalupe' in name should not duplicate hispanic."""
        from backend.data.cuisine_tags import infer_cuisine_tags

        pantry = {"name": "Guadalupe Centers", "languages": ["en", "es"], "type": "pantry"}
        tags = infer_cuisine_tags(pantry)
        assert tags.count("hispanic") == 1

    def test_returns_list_type(self) -> None:
        from backend.data.cuisine_tags import infer_cuisine_tags

        pantry = {"name": "Test", "type": "pantry"}
        result = infer_cuisine_tags(pantry)
        assert isinstance(result, list)


class TestEnrichPantryCuisineTags:
    """enrich_pantry_cuisine_tags prefers static map, falls back to heuristic."""

    def test_static_map_preferred_over_heuristic(self) -> None:
        from backend.data.cuisine_tags import PANTRY_CUISINE_MAP, enrich_pantry_cuisine_tags

        # Use a known static ID
        pantry = {"id": "p1", "name": "Harvesters", "languages": ["en"], "type": "pantry"}
        tags = enrich_pantry_cuisine_tags(pantry)
        assert tags == PANTRY_CUISINE_MAP["p1"]

    def test_unknown_id_falls_back_to_heuristic(self) -> None:
        from backend.data.cuisine_tags import enrich_pantry_cuisine_tags

        pantry = {"id": "unknown_999", "name": "New Pantry", "languages": ["en"], "type": "pantry"}
        tags = enrich_pantry_cuisine_tags(pantry)
        assert tags == ["american"]

    def test_missing_id_falls_back_to_heuristic(self) -> None:
        from backend.data.cuisine_tags import enrich_pantry_cuisine_tags

        pantry = {"name": "No ID Pantry", "languages": ["en", "es"], "type": "pantry"}
        tags = enrich_pantry_cuisine_tags(pantry)
        assert "american" in tags
        assert "hispanic" in tags

    def test_static_map_p5_includes_soul_food(self) -> None:
        from backend.data.cuisine_tags import enrich_pantry_cuisine_tags

        pantry = {"id": "p5", "name": "Community Fridge Troost", "type": "pantry"}
        tags = enrich_pantry_cuisine_tags(pantry)
        assert "soul_food" in tags

    def test_static_map_s1_includes_all_five(self) -> None:
        from backend.data.cuisine_tags import enrich_pantry_cuisine_tags

        pantry = {"id": "s1", "name": "Price Chopper", "type": "store"}
        tags = enrich_pantry_cuisine_tags(pantry)
        assert set(tags) == {"american", "hispanic", "asian", "african_caribbean", "soul_food"}

    def test_static_map_d1_includes_all_five(self) -> None:
        from backend.data.cuisine_tags import enrich_pantry_cuisine_tags

        pantry = {"id": "d1", "name": "Walmart Delivery", "type": "delivery"}
        tags = enrich_pantry_cuisine_tags(pantry)
        assert set(tags) == {"american", "hispanic", "asian", "african_caribbean", "soul_food"}


class TestPantryCuisineMap:
    """Validate specific entries in the static map."""

    def test_p1_harvesters(self) -> None:
        from backend.data.cuisine_tags import PANTRY_CUISINE_MAP

        assert PANTRY_CUISINE_MAP["p1"] == ["american", "hispanic"]

    def test_p2_restart(self) -> None:
        from backend.data.cuisine_tags import PANTRY_CUISINE_MAP

        assert PANTRY_CUISINE_MAP["p2"] == ["american"]

    def test_p6_guadalupe(self) -> None:
        from backend.data.cuisine_tags import PANTRY_CUISINE_MAP

        assert PANTRY_CUISINE_MAP["p6"] == ["hispanic", "american"]

    def test_s2_save_a_lot(self) -> None:
        from backend.data.cuisine_tags import PANTRY_CUISINE_MAP

        assert PANTRY_CUISINE_MAP["s2"] == ["american", "soul_food"]
