"""
Tests for the community vote feature — curveball deliverable #2.

VoteZone and CommunityVote schemas, _build_community_vote() logic,
and API integration.
"""
from __future__ import annotations

import pytest


class TestVoteZoneSchema:
    """VoteZone Pydantic model validates correctly."""

    def test_valid_vote_zone(self) -> None:
        from backend.models.schemas import VoteZone

        zone = VoteZone(
            zip="66101",
            need_score=89,
            spanish_dominant=True,
            label="Argentine / KCK",
        )
        assert zone.zip == "66101"
        assert zone.need_score == 89
        assert zone.spanish_dominant is True
        assert zone.label == "Argentine / KCK"

    def test_vote_zone_requires_all_fields(self) -> None:
        from pydantic import ValidationError
        from backend.models.schemas import VoteZone

        with pytest.raises(ValidationError):
            VoteZone(zip="66101")  # type: ignore[call-arg]


class TestCommunityVoteSchema:
    """CommunityVote Pydantic model validates correctly."""

    def test_default_values(self) -> None:
        from backend.models.schemas import CommunityVote

        vote = CommunityVote(deadline="2026-04-11")
        assert vote.active is True
        assert vote.deadline == "2026-04-11"
        assert vote.zones == []
        assert vote.total_zones == 2

    def test_with_zones(self) -> None:
        from backend.models.schemas import CommunityVote, VoteZone

        zones = [
            VoteZone(zip="66101", need_score=89, spanish_dominant=True, label="Argentine / KCK"),
            VoteZone(zip="64130", need_score=82, spanish_dominant=False, label="Ivanhoe / KCMO"),
        ]
        vote = CommunityVote(deadline="2026-04-11", zones=zones)
        assert len(vote.zones) == 2
        assert vote.zones[0].zip == "66101"


class TestOptionsResponseIncludesCommunityVote:
    """OptionsResponse schema has community_vote field."""

    def test_community_vote_field_exists(self) -> None:
        from backend.models.schemas import OptionsResponse

        fields = OptionsResponse.model_fields
        assert "community_vote" in fields

    def test_community_vote_defaults_to_none(self) -> None:
        from backend.models.schemas import OptionsResponse, ProduceAlert

        resp = OptionsResponse(
            zip="64130",
            need_score=82,
            options=[],
            produce_alert=ProduceAlert(active=False),
        )
        assert resp.community_vote is None

    def test_community_vote_accepts_value(self) -> None:
        from backend.models.schemas import (
            CommunityVote,
            OptionsResponse,
            ProduceAlert,
            VoteZone,
        )

        vote = CommunityVote(
            deadline="2026-04-11",
            zones=[
                VoteZone(zip="66101", need_score=89, spanish_dominant=True, label="Test"),
            ],
        )
        resp = OptionsResponse(
            zip="64130",
            need_score=82,
            options=[],
            produce_alert=ProduceAlert(active=False),
            community_vote=vote,
        )
        assert resp.community_vote is not None
        assert resp.community_vote.deadline == "2026-04-11"
        assert len(resp.community_vote.zones) == 1


class TestBuildCommunityVote:
    """_build_community_vote() logic in options.py."""

    def test_returns_community_vote_when_harvest_zips_exist(self) -> None:
        from backend.api.options import _build_community_vote

        result = _build_community_vote()
        # harvest_zips is loaded from the API; if non-empty we get a CommunityVote
        from backend.data.cache import AppCache

        if AppCache.harvest_zips:
            assert result is not None
            assert result.active is True
            assert result.deadline == "2026-04-11"
            assert len(result.zones) <= 2
            assert result.total_zones == 2
        else:
            assert result is None

    def test_returns_none_when_harvest_zips_empty(self) -> None:
        from backend.data.cache import AppCache
        from backend.api.options import _build_community_vote

        original = AppCache.harvest_zips
        try:
            AppCache.harvest_zips = set()
            result = _build_community_vote()
            assert result is None
        finally:
            AppCache.harvest_zips = original

    def test_zones_sorted_by_need_score_descending(self) -> None:
        from backend.data.cache import AppCache
        from backend.api.options import _build_community_vote

        if not AppCache.harvest_zips:
            pytest.skip("No harvest ZIPs in cache")

        result = _build_community_vote()
        assert result is not None
        scores = [z.need_score for z in result.zones]
        assert scores == sorted(scores, reverse=True)

    def test_spanish_dominant_flags_correct_zips(self) -> None:
        from backend.data.cache import AppCache
        from backend.api.options import _build_community_vote

        # Inject known ZIPs to guarantee the test is deterministic
        original_harvest = AppCache.harvest_zips
        original_scores = AppCache.need_scores.copy()
        try:
            AppCache.harvest_zips = {"66101", "64130"}
            # Ensure both have scores
            AppCache.need_scores["66101"] = 90
            AppCache.need_scores["64130"] = 80

            result = _build_community_vote()
            assert result is not None

            zone_map = {z.zip: z for z in result.zones}
            # 66101 is in the Spanish-dominant set
            assert zone_map["66101"].spanish_dominant is True
            # 64130 is NOT in the Spanish-dominant set
            assert zone_map["64130"].spanish_dominant is False
        finally:
            AppCache.harvest_zips = original_harvest
            AppCache.need_scores.update(original_scores)

    def test_zones_capped_at_two(self) -> None:
        from backend.data.cache import AppCache
        from backend.api.options import _build_community_vote

        original = AppCache.harvest_zips
        original_scores = AppCache.need_scores.copy()
        try:
            AppCache.harvest_zips = {"66101", "64130", "64108", "66105"}
            for z in AppCache.harvest_zips:
                AppCache.need_scores.setdefault(z, 50)
            result = _build_community_vote()
            assert result is not None
            assert len(result.zones) == 2
        finally:
            AppCache.harvest_zips = original
            AppCache.need_scores.update(original_scores)


class TestApiReturnsCommunityVote:
    """GET /api/options includes community_vote in the response."""

    def test_community_vote_present_in_response(self) -> None:
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)
        resp = client.get("/api/options?zip=64130")
        assert resp.status_code == 200

        data = resp.json()
        assert "community_vote" in data

    def test_community_vote_structure_when_active(self) -> None:
        from fastapi.testclient import TestClient
        from backend.main import app
        from backend.data.cache import AppCache

        if not AppCache.harvest_zips:
            pytest.skip("No harvest ZIPs — community_vote will be null")

        client = TestClient(app)
        resp = client.get("/api/options?zip=64130")
        data = resp.json()

        cv = data["community_vote"]
        assert cv is not None
        assert cv["active"] is True
        assert cv["deadline"] == "2026-04-11"
        assert isinstance(cv["zones"], list)
        assert cv["total_zones"] == 2

        for zone in cv["zones"]:
            assert "zip" in zone
            assert "need_score" in zone
            assert "spanish_dominant" in zone
            assert "label" in zone
