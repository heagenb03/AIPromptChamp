"""
Cuisine tagging system for food access options.

Provides a static mapping of known pantry/store IDs to cuisine tags,
plus a heuristic inference function for unknown pantries based on
language offerings and name keywords.
"""
from __future__ import annotations

import re

VALID_CUISINES: frozenset[str] = frozenset(
    {"american", "hispanic", "asian", "african_caribbean", "soul_food"}
)

ALL_CUISINES_LIST: list[str] = sorted(VALID_CUISINES)

# Static cuisine tags for known pantry/store/delivery IDs.
PANTRY_CUISINE_MAP: dict[str, list[str]] = {
    "p1": ["american", "hispanic"],                                      # Harvesters
    "p2": ["american"],                                                  # Restart Inc
    "p3": ["american", "hispanic"],                                      # Catholic Charities
    "p4": ["american"],                                                  # Operation Breakthrough
    "p5": ["american", "hispanic", "soul_food"],                         # Community Fridge Troost
    "p6": ["hispanic", "american"],                                      # Guadalupe Centers
    "s1": ["american", "hispanic", "asian", "african_caribbean", "soul_food"],  # Price Chopper
    "s2": ["american", "soul_food"],                                     # Save-A-Lot
    "d1": ["american", "hispanic", "asian", "african_caribbean", "soul_food"],  # Walmart Delivery
}

# Keywords in pantry name that indicate Hispanic cuisine (case-insensitive).
_HISPANIC_NAME_PATTERN: re.Pattern[str] = re.compile(
    r"guadalupe|chavez|hispanic|latino|mexican", re.IGNORECASE
)


def infer_cuisine_tags(pantry: dict) -> list[str]:
    """
    Heuristic inference of cuisine tags for a pantry not in the static map.

    Rules:
    1. Always include "american".
    2. If "es" in languages -> add "hispanic".
    3. If name matches Hispanic keywords -> add "hispanic".
    4. If type is "store" or "delivery" -> add all 5 cuisines.
    """
    pantry_type = pantry.get("type", "pantry")

    # Stores and delivery providers carry all cuisines
    if pantry_type in ("store", "delivery"):
        return list(ALL_CUISINES_LIST)

    tags: list[str] = ["american"]

    # Check language offerings
    languages = pantry.get("languages", [])
    has_hispanic = "es" in languages

    # Check name for Hispanic keywords
    name = pantry.get("name", "")
    if _HISPANIC_NAME_PATTERN.search(name):
        has_hispanic = True

    if has_hispanic:
        tags.append("hispanic")

    return tags


def enrich_pantry_cuisine_tags(pantry: dict) -> list[str]:
    """
    Return cuisine tags for a pantry. Checks the static map first by ID,
    then falls back to heuristic inference.
    """
    pantry_id = pantry.get("id", "")
    if pantry_id and pantry_id in PANTRY_CUISINE_MAP:
        return list(PANTRY_CUISINE_MAP[pantry_id])
    return infer_cuisine_tags(pantry)
