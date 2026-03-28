"""Tests for POST /api/parse-query — NLP ZIP extraction endpoint."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app, raise_server_exceptions=True)


def _claude_ok(zip_val: str, confidence: str = "high", interpreted_as: str = "") -> dict:
    return {"zip": zip_val, "confidence": confidence, "interpreted_as": interpreted_as or f"ZIP {zip_val}"}


def _claude_null(error: str = "Could not determine a KC ZIP from your input") -> dict:
    return {"zip": None, "error": error}


class TestParseQueryEndpoint:
    def test_explicit_kcmo_zip_returns_zip(self):
        with patch("backend.api.parse_query._call_claude", return_value=_claude_ok("64130")):
            r = client.post("/api/parse-query", json={"query": "64130"})
        assert r.status_code == 200
        data = r.json()
        assert data["zip"] == "64130"
        assert data["confidence"] == "high"

    def test_explicit_kck_zip_accepted(self):
        with patch("backend.api.parse_query._call_claude", return_value=_claude_ok("66101")):
            r = client.post("/api/parse-query", json={"query": "food in KCK"})
        assert r.status_code == 200
        assert r.json()["zip"] == "66101"

    def test_neighborhood_name_returns_low_confidence_zip(self):
        with patch(
            "backend.api.parse_query._call_claude",
            return_value=_claude_ok("64108", "low", "Westside Kansas City, MO"),
        ):
            r = client.post("/api/parse-query", json={"query": "I need groceries near Westside KC"})
        assert r.status_code == 200
        data = r.json()
        assert data["zip"] == "64108"
        assert data["confidence"] == "low"
        assert "Westside" in data["interpreted_as"]

    def test_unknown_location_returns_null_zip(self):
        with patch("backend.api.parse_query._call_claude", return_value=_claude_null()):
            r = client.post("/api/parse-query", json={"query": "somewhere on the moon"})
        assert r.status_code == 200
        data = r.json()
        assert data["zip"] is None
        assert data["error"] is not None

    def test_empty_query_returns_null_without_calling_claude(self):
        with patch("backend.api.parse_query._call_claude") as mock_claude:
            r = client.post("/api/parse-query", json={"query": "   "})
        assert r.status_code == 200
        assert r.json()["zip"] is None
        mock_claude.assert_not_called()

    def test_whitespace_only_query_returns_error(self):
        r = client.post("/api/parse-query", json={"query": "   "})
        assert r.json()["error"] is not None

    def test_missing_body_returns_422(self):
        r = client.post("/api/parse-query")
        assert r.status_code == 422

    def test_missing_query_field_returns_422(self):
        r = client.post("/api/parse-query", json={})
        assert r.status_code == 422

    def test_non_kc_zip_from_claude_is_rejected(self):
        """Claude hallucinating a non-KC ZIP must be caught and nulled."""
        with patch(
            "backend.api.parse_query._call_claude",
            return_value={"zip": "10001", "confidence": "low", "interpreted_as": "New York"},
        ):
            r = client.post("/api/parse-query", json={"query": "midtown"})
        assert r.status_code == 200
        data = r.json()
        assert data["zip"] is None

    def test_no_api_key_returns_503(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        r = client.post("/api/parse-query", json={"query": "food near 64130"})
        assert r.status_code == 503

    def test_claude_json_decode_error_returns_graceful_null(self):
        with patch(
            "backend.api.parse_query._call_claude",
            side_effect=json.JSONDecodeError("bad json", "", 0),
        ):
            r = client.post("/api/parse-query", json={"query": "near troost"})
        assert r.status_code == 200
        data = r.json()
        assert data["zip"] is None
        assert "ZIP code" in data["error"]

    def test_claude_unexpected_error_returns_503(self):
        with patch(
            "backend.api.parse_query._call_claude",
            side_effect=RuntimeError("network blip"),
        ):
            r = client.post("/api/parse-query", json={"query": "food near downtown"})
        assert r.status_code == 503

    def test_response_has_all_fields(self):
        with patch("backend.api.parse_query._call_claude", return_value=_claude_ok("64130")):
            r = client.post("/api/parse-query", json={"query": "64130"})
        data = r.json()
        assert "zip" in data
        assert "confidence" in data
        assert "interpreted_as" in data
        assert "error" in data

    def test_query_over_500_chars_returns_422(self):
        """max_length=500 on ParseQueryRequest.query."""
        r = client.post("/api/parse-query", json={"query": "x" * 501})
        assert r.status_code == 422

    def test_query_exactly_500_chars_is_accepted(self):
        with patch("backend.api.parse_query._call_claude", return_value=_claude_ok("64130")):
            r = client.post("/api/parse-query", json={"query": "a" * 500})
        assert r.status_code == 200

    def test_unexpected_confidence_value_coerced_to_none(self):
        """Claude returning an unknown confidence string must not 500."""
        with patch(
            "backend.api.parse_query._call_claude",
            return_value={"zip": "64130", "confidence": "medium", "interpreted_as": "x"},
        ):
            r = client.post("/api/parse-query", json={"query": "64130"})
        assert r.status_code == 200
        assert r.json()["confidence"] is None

    def test_markdown_fenced_json_is_handled(self):
        """Claude sometimes wraps JSON in ```json ... ``` — must still parse correctly."""
        fenced = '```json\n{"zip": "64130", "confidence": "high", "interpreted_as": "explicit"}\n```'
        with patch(
            "backend.api.parse_query._call_claude",
            wraps=lambda q: json.loads(q),  # bypass; test _extract_json directly
        ):
            from backend.api.parse_query import _extract_json
            result = json.loads(_extract_json(fenced))
        assert result["zip"] == "64130"

    def test_sanitize_query_strips_injection_chars(self):
        """Characters outside the allowed set are stripped before Claude sees them."""
        from backend.api.parse_query import _sanitize_query

        assert _sanitize_query("64130\x00<script>") == "64130script"
        assert _sanitize_query("Troost & Paseo!") == "Troost  Paseo"
        # Allowed characters survive
        assert _sanitize_query("food near 64130, KC") == "food near 64130, KC"
