"""POST /api/parse-query — NLP ZIP code extraction using Claude Haiku."""
from __future__ import annotations

import json
import logging
import os
import re

import anthropic
from fastapi import APIRouter, HTTPException

from backend.models.schemas import ParseQueryRequest, ParseQueryResponse

router = APIRouter()
logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a location parser for a Kansas City food access app.

Valid KC ZIP codes: 641xx (KCMO) or 661xx (KCK — Kansas City, Kansas).

Task: extract or infer a valid KC ZIP from the user's input.

Rules:
1. Explicit 5-digit ZIP starting with 641 or 661 → return it, confidence "high".
2. KC neighborhood or landmark → infer most likely ZIP, confidence "low".
3. Cannot determine a KC ZIP → return zip null with an error message.

KC neighborhood → ZIP reference (partial):
  Downtown / River Market: 64101, 64105
  Westside / SW Boulevard: 64108
  Midtown / Crossroads:    64108, 64111
  Hyde Park / Troost:      64110
  Paseo / Blue Hills:      64130
  Swope Park area:         64132
  Independence Ave / NE:   64124
  Waldo / Brookside:       64114
  Northland / North KC:    64150, 64151
  KCK / Argentine:         66101, 66102
  KCK / Armourdale:        66101, 66105

Examples:
{"zip": "64130", "confidence": "high", "interpreted_as": "explicit ZIP 64130"}
{"zip": "64108", "confidence": "low",  "interpreted_as": "Westside Kansas City, MO"}
{"zip": null, "error": "Could not determine a KC ZIP from your input"}

Return ONLY valid JSON, no prose.
"""

_VALID_ZIP_PREFIXES = ("641", "661")
# Cached client — created once on first use (avoids per-request connection pool setup)
_anthropic_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    """Return a cached Anthropic client, raising 503 if the key is absent."""
    global _anthropic_client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="NLP service not configured (missing API key).")
    if _anthropic_client is None:
        _anthropic_client = anthropic.Anthropic(api_key=api_key)
    return _anthropic_client


_QUERY_SANITIZE_RE = re.compile(r"[^\w\s,.\-#'/]")


def _sanitize_query(query: str) -> str:
    """Strip characters that have no business in a location query."""
    return _QUERY_SANITIZE_RE.sub("", query)


_MARKDOWN_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _extract_json(raw: str) -> str:
    """Strip markdown code fences if Claude wrapped the JSON in one."""
    return _MARKDOWN_FENCE_RE.sub("", raw).strip()


def _call_claude(query: str) -> dict[str, object]:
    """Call Claude Haiku to parse a natural language location query into a KC ZIP."""
    client = _get_client()
    safe_query = _sanitize_query(query)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": safe_query}],
        timeout=10.0,
    )
    if not message.content:
        raise ValueError("Claude returned empty content block")
    raw = message.content[0].text.strip()
    logger.debug("Claude raw response: %r", raw)
    return json.loads(_extract_json(raw))


@router.post("/parse-query", response_model=ParseQueryResponse)
def parse_query(body: ParseQueryRequest) -> ParseQueryResponse:
    # NOTE: This is a sync handler — FastAPI runs it in a threadpool. For a hackathon
    # this is fine; switch to async + AsyncAnthropic for higher-concurrency production use.
    query = body.query.strip()
    if not query:
        return ParseQueryResponse(zip=None, error="Query cannot be empty.")

    try:
        result = _call_claude(query)
    except HTTPException:
        raise
    except json.JSONDecodeError as exc:
        logger.error("Claude returned non-JSON (%s). Raw response logged at DEBUG level.", exc)
        return ParseQueryResponse(zip=None, error="Could not parse location. Please try a ZIP code.")
    except Exception as exc:
        logger.error("Claude API error: %s", exc)
        raise HTTPException(status_code=503, detail="NLP service temporarily unavailable.")

    zip_val = result.get("zip")

    # Validate that Claude only returns a real KC ZIP
    if zip_val is not None and (
        not isinstance(zip_val, str)
        or len(zip_val) != 5
        or not zip_val.isdigit()
        or not zip_val.startswith(_VALID_ZIP_PREFIXES)
    ):
        return ParseQueryResponse(zip=None, error="Could not find a KC location. Try a ZIP code.")

    # Guard against unexpected confidence values (Pydantic Literal would 500 otherwise)
    raw_confidence = result.get("confidence")
    confidence = raw_confidence if raw_confidence in ("high", "low") else None

    return ParseQueryResponse(
        zip=zip_val,
        confidence=confidence,
        interpreted_as=result.get("interpreted_as"),
        error=result.get("error"),
    )
