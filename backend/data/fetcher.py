"""
Fetches data from all challenge API endpoints.

The base URL is read from the CHALLENGE_API_BASE environment variable.
Falls back to mock data if the env var is not set or a request fails,
so development works offline before the competition APIs are live.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_BASE_URL = os.getenv("CHALLENGE_API_BASE", "").rstrip("/")
_TIMEOUT = 10.0  # seconds per request


def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    """HTTP GET against the challenge API. Returns parsed JSON."""
    url = f"{_BASE_URL}{path}"
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("API fetch failed for %s: %s — using mock data", path, exc)
        return None


# ---------------------------------------------------------------------------
# Individual endpoint fetchers
# ---------------------------------------------------------------------------

def fetch_pantries() -> list[dict]:
    data = _get("/challenge/pantries")
    if data is not None:
        return data
    return _mock_pantries()


def fetch_food_atlas() -> list[dict]:
    data = _get("/challenge/food-atlas")
    if data is not None:
        return data
    return _mock_food_atlas()


def fetch_demographics() -> list[dict]:
    data = _get("/challenge/demographics")
    if data is not None:
        return data
    return _mock_demographics()


def fetch_311_calls() -> list[dict]:
    data = _get("/challenge/311-calls")
    if data is not None:
        return data
    return _mock_311_calls()


def fetch_store_closures() -> list[dict]:
    data = _get("/challenge/store-closures")
    if data is not None:
        return data
    return _mock_store_closures()


def fetch_transit() -> list[dict]:
    data = _get("/challenge/transit")
    if data is not None:
        return data
    return _mock_transit()


def fetch_supply_alerts() -> dict:
    data = _get("/challenge/supply-alerts")
    if data is not None:
        return data
    return _mock_supply_alerts()


def fetch_harvest() -> dict:
    data = _get("/challenge/harvest")
    if data is not None:
        return data
    return _mock_harvest()


# ---------------------------------------------------------------------------
# Mock data — realistic KC data used when APIs are unavailable
# ---------------------------------------------------------------------------

def _mock_pantries() -> list[dict]:
    return [
        {
            "id": "p1",
            "name": "Harvesters Food Network",
            "address": "3801 Topping Ave, Kansas City, MO 64129",
            "zip": "64129",
            "lat": 39.0628,
            "lng": -94.5317,
            "hours": "Mon-Fri 9AM-5PM",
            "languages": ["en", "es"],
            "id_required": False,
            "cold_storage": True,
            "transit_stop_ids": ["kc-bus-42", "kc-bus-51"],
        },
        {
            "id": "p2",
            "name": "Restart Inc Food Pantry",
            "address": "918 E 9th St, Kansas City, MO 64106",
            "zip": "64106",
            "lat": 39.1001,
            "lng": -94.5710,
            "hours": "Mon/Wed/Fri 10AM-2PM",
            "languages": ["en"],
            "id_required": True,
            "cold_storage": False,
            "transit_stop_ids": ["kc-bus-12"],
        },
        {
            "id": "p3",
            "name": "Catholic Charities of KC–St. Joseph",
            "address": "1112 Broadway Blvd, Kansas City, MO 64105",
            "zip": "64105",
            "lat": 39.1016,
            "lng": -94.5782,
            "hours": "Tue/Thu 9AM-12PM",
            "languages": ["en", "es"],
            "id_required": False,
            "cold_storage": True,
            "transit_stop_ids": ["kc-bus-12", "kc-bus-19"],
        },
        {
            "id": "p4",
            "name": "Operation Breakthrough",
            "address": "3039 Troost Ave, Kansas City, MO 64109",
            "zip": "64109",
            "lat": 39.0771,
            "lng": -94.5636,
            "hours": "Mon-Fri 8AM-4PM",
            "languages": ["en"],
            "id_required": False,
            "cold_storage": False,
            "transit_stop_ids": ["kc-bus-31"],
        },
        {
            "id": "p5",
            "name": "KCMO Community Fridge – Troost",
            "address": "3500 Troost Ave, Kansas City, MO 64109",
            "zip": "64109",
            "lat": 39.0748,
            "lng": -94.5636,
            "hours": "24/7",
            "languages": ["en", "es"],
            "id_required": False,
            "cold_storage": True,
            "transit_stop_ids": ["kc-bus-31"],
        },
        {
            "id": "p6",
            "name": "Guadalupe Centers Food Pantry",
            "address": "1015 Avenida Cesar E Chavez, Kansas City, MO 64108",
            "zip": "64108",
            "lat": 39.0955,
            "lng": -94.5768,
            "hours": "Mon/Wed 9AM-1PM",
            "languages": ["en", "es"],
            "id_required": False,
            "cold_storage": True,
            "transit_stop_ids": ["kc-bus-24", "kc-bus-51"],
        },
        {
            "id": "s1",
            "name": "Price Chopper",
            "type": "store",
            "address": "4000 Main St, Kansas City, MO 64111",
            "zip": "64111",
            "lat": 39.0618,
            "lng": -94.5807,
            "cost_tier": "low",
            "est_cost_weekly": "$40-60",
            "snap_eligible": True,
            "transit_stop_ids": ["kc-bus-47"],
        },
        {
            "id": "s2",
            "name": "Save-A-Lot",
            "type": "store",
            "address": "3039 Prospect Ave, Kansas City, MO 64128",
            "zip": "64128",
            "lat": 39.0631,
            "lng": -94.5503,
            "cost_tier": "low",
            "est_cost_weekly": "$30-45",
            "snap_eligible": True,
            "transit_stop_ids": ["kc-bus-31", "kc-bus-55"],
        },
        {
            "id": "d1",
            "name": "Walmart Grocery Delivery",
            "type": "delivery",
            "address": None,
            "zip": None,
            "lat": None,
            "lng": None,
            "cost_tier": "market",
            "est_cost_order": "$35+",
            "delivery_fee": "$7.95",
            "snap_eligible": True,
            "languages": ["en"],
        },
    ]


def _mock_food_atlas() -> list[dict]:
    """Food desert severity score per ZIP (0=none, 10=severe)."""
    return [
        {"zip": "64101", "food_desert_severity": 7.2},
        {"zip": "64105", "food_desert_severity": 5.1},
        {"zip": "64106", "food_desert_severity": 6.8},
        {"zip": "64108", "food_desert_severity": 8.4},
        {"zip": "64109", "food_desert_severity": 7.9},
        {"zip": "64110", "food_desert_severity": 4.3},
        {"zip": "64111", "food_desert_severity": 3.0},
        {"zip": "64112", "food_desert_severity": 1.2},
        {"zip": "64113", "food_desert_severity": 2.1},
        {"zip": "64114", "food_desert_severity": 3.5},
        {"zip": "64120", "food_desert_severity": 7.6},
        {"zip": "64123", "food_desert_severity": 8.1},
        {"zip": "64124", "food_desert_severity": 8.9},
        {"zip": "64125", "food_desert_severity": 7.3},
        {"zip": "64126", "food_desert_severity": 8.7},
        {"zip": "64127", "food_desert_severity": 9.1},
        {"zip": "64128", "food_desert_severity": 8.5},
        {"zip": "64129", "food_desert_severity": 7.8},
        {"zip": "64130", "food_desert_severity": 9.2},
        {"zip": "64131", "food_desert_severity": 4.6},
        {"zip": "64132", "food_desert_severity": 6.2},
        {"zip": "64133", "food_desert_severity": 5.4},
        {"zip": "64134", "food_desert_severity": 5.8},
        {"zip": "64136", "food_desert_severity": 4.9},
        {"zip": "64137", "food_desert_severity": 5.3},
        {"zip": "64138", "food_desert_severity": 5.1},
        {"zip": "64139", "food_desert_severity": 4.7},
        {"zip": "64145", "food_desert_severity": 3.2},
        {"zip": "64146", "food_desert_severity": 2.8},
        {"zip": "64147", "food_desert_severity": 3.6},
        {"zip": "64149", "food_desert_severity": 4.1},
        {"zip": "64150", "food_desert_severity": 2.4},
        {"zip": "64151", "food_desert_severity": 2.7},
        {"zip": "64152", "food_desert_severity": 1.8},
        {"zip": "64153", "food_desert_severity": 2.1},
        {"zip": "64154", "food_desert_severity": 2.3},
        {"zip": "64155", "food_desert_severity": 1.9},
        {"zip": "64156", "food_desert_severity": 2.0},
        {"zip": "64157", "food_desert_severity": 1.6},
        {"zip": "64158", "food_desert_severity": 1.5},
        {"zip": "64161", "food_desert_severity": 3.8},
        {"zip": "64163", "food_desert_severity": 3.2},
        {"zip": "64164", "food_desert_severity": 3.0},
        {"zip": "64165", "food_desert_severity": 2.6},
        {"zip": "64166", "food_desert_severity": 2.4},
        {"zip": "64167", "food_desert_severity": 2.2},
        {"zip": "64168", "food_desert_severity": 1.4},
    ]


def _mock_demographics() -> list[dict]:
    """Poverty rate (0–1) and % households with no vehicle (0–1) per ZIP."""
    return [
        {"zip": "64101", "poverty_rate": 0.31, "no_vehicle_pct": 0.28},
        {"zip": "64105", "poverty_rate": 0.22, "no_vehicle_pct": 0.21},
        {"zip": "64106", "poverty_rate": 0.29, "no_vehicle_pct": 0.33},
        {"zip": "64108", "poverty_rate": 0.38, "no_vehicle_pct": 0.42},
        {"zip": "64109", "poverty_rate": 0.35, "no_vehicle_pct": 0.38},
        {"zip": "64110", "poverty_rate": 0.18, "no_vehicle_pct": 0.19},
        {"zip": "64111", "poverty_rate": 0.12, "no_vehicle_pct": 0.14},
        {"zip": "64112", "poverty_rate": 0.06, "no_vehicle_pct": 0.08},
        {"zip": "64113", "poverty_rate": 0.08, "no_vehicle_pct": 0.09},
        {"zip": "64114", "poverty_rate": 0.10, "no_vehicle_pct": 0.11},
        {"zip": "64120", "poverty_rate": 0.33, "no_vehicle_pct": 0.31},
        {"zip": "64123", "poverty_rate": 0.37, "no_vehicle_pct": 0.36},
        {"zip": "64124", "poverty_rate": 0.41, "no_vehicle_pct": 0.44},
        {"zip": "64125", "poverty_rate": 0.32, "no_vehicle_pct": 0.30},
        {"zip": "64126", "poverty_rate": 0.39, "no_vehicle_pct": 0.41},
        {"zip": "64127", "poverty_rate": 0.43, "no_vehicle_pct": 0.47},
        {"zip": "64128", "poverty_rate": 0.40, "no_vehicle_pct": 0.43},
        {"zip": "64129", "poverty_rate": 0.34, "no_vehicle_pct": 0.37},
        {"zip": "64130", "poverty_rate": 0.44, "no_vehicle_pct": 0.48},
        {"zip": "64131", "poverty_rate": 0.14, "no_vehicle_pct": 0.13},
        {"zip": "64132", "poverty_rate": 0.26, "no_vehicle_pct": 0.24},
        {"zip": "64133", "poverty_rate": 0.20, "no_vehicle_pct": 0.18},
        {"zip": "64134", "poverty_rate": 0.22, "no_vehicle_pct": 0.20},
        {"zip": "64136", "poverty_rate": 0.17, "no_vehicle_pct": 0.15},
        {"zip": "64137", "poverty_rate": 0.19, "no_vehicle_pct": 0.17},
        {"zip": "64138", "poverty_rate": 0.18, "no_vehicle_pct": 0.16},
        {"zip": "64145", "poverty_rate": 0.09, "no_vehicle_pct": 0.08},
        {"zip": "64150", "poverty_rate": 0.08, "no_vehicle_pct": 0.07},
        {"zip": "64151", "poverty_rate": 0.09, "no_vehicle_pct": 0.08},
        {"zip": "64152", "poverty_rate": 0.05, "no_vehicle_pct": 0.05},
    ]


def _mock_311_calls() -> list[dict]:
    """Housing/utility distress call volume per ZIP (last 90 days)."""
    return [
        {"zip": "64101", "distress_calls": 87},
        {"zip": "64105", "distress_calls": 52},
        {"zip": "64106", "distress_calls": 74},
        {"zip": "64108", "distress_calls": 143},
        {"zip": "64109", "distress_calls": 121},
        {"zip": "64110", "distress_calls": 48},
        {"zip": "64111", "distress_calls": 31},
        {"zip": "64112", "distress_calls": 12},
        {"zip": "64113", "distress_calls": 15},
        {"zip": "64114", "distress_calls": 22},
        {"zip": "64120", "distress_calls": 98},
        {"zip": "64123", "distress_calls": 112},
        {"zip": "64124", "distress_calls": 156},
        {"zip": "64125", "distress_calls": 89},
        {"zip": "64126", "distress_calls": 134},
        {"zip": "64127", "distress_calls": 167},
        {"zip": "64128", "distress_calls": 148},
        {"zip": "64129", "distress_calls": 103},
        {"zip": "64130", "distress_calls": 178},
        {"zip": "64131", "distress_calls": 28},
        {"zip": "64132", "distress_calls": 61},
        {"zip": "64133", "distress_calls": 44},
        {"zip": "64134", "distress_calls": 49},
        {"zip": "64145", "distress_calls": 18},
        {"zip": "64150", "distress_calls": 14},
        {"zip": "64151", "distress_calls": 17},
        {"zip": "64152", "distress_calls": 9},
    ]


def _mock_store_closures() -> list[dict]:
    """Recent grocery store closures per ZIP (last 24 months)."""
    return [
        {"zip": "64108", "closures": 2},
        {"zip": "64109", "closures": 1},
        {"zip": "64124", "closures": 3},
        {"zip": "64126", "closures": 2},
        {"zip": "64127", "closures": 2},
        {"zip": "64128", "closures": 1},
        {"zip": "64130", "closures": 3},
        {"zip": "64132", "closures": 1},
    ]


def _mock_transit() -> list[dict]:
    """Bus stop data with frequency (trips/hour) for routing scoring."""
    return [
        {"stop_id": "kc-bus-12", "name": "12th St & Grand", "trips_per_hour": 6},
        {"stop_id": "kc-bus-19", "name": "19th & Main", "trips_per_hour": 4},
        {"stop_id": "kc-bus-24", "name": "Cesar Chavez & Southwest Blvd", "trips_per_hour": 5},
        {"stop_id": "kc-bus-31", "name": "Troost & 31st", "trips_per_hour": 8},
        {"stop_id": "kc-bus-42", "name": "Topping & 39th", "trips_per_hour": 3},
        {"stop_id": "kc-bus-47", "name": "Main & 43rd", "trips_per_hour": 5},
        {"stop_id": "kc-bus-51", "name": "Prospect & 51st", "trips_per_hour": 4},
        {"stop_id": "kc-bus-55", "name": "Prospect & Gregory", "trips_per_hour": 3},
    ]


def _mock_supply_alerts() -> dict:
    """Active fresh produce donation alerts."""
    return {
        "active": True,
        "item": "fresh produce",
        "pounds": 1000,
        "expires_in_hrs": 48,
        "donated_by": "After the Harvest",
        "available_from": "2026-03-28T10:00:00",
    }


def _mock_harvest() -> dict:
    """After the Harvest priority ZIPs for food rescue."""
    return {
        "priority_zips": ["64130", "64127", "64124", "64128", "64108"],
        "description": "High-need ZIPs flagged for priority food rescue routing",
    }
