"""Static KC delivery providers and ZIP filtering."""
from __future__ import annotations


_STATIC_PROVIDERS: list[dict] = [
    {
        "name": "Walmart Grocery",
        "snap_accepted": True,
        "ebt_accepted": True,
        "delivery_fee": 7.95,
        "order_minimum": 35.00,
        "same_day": True,
        "cost_tier": "low",
        "notes": "SNAP/EBT accepted at checkout",
    },
    {
        "name": "Amazon Fresh",
        "snap_accepted": True,
        "ebt_accepted": True,
        "delivery_fee": 9.95,
        "order_minimum": 35.00,
        "same_day": True,
        "cost_tier": "market",
        "notes": "Free delivery with Prime; EBT accepted",
    },
    {
        "name": "Instacart (Aldi/Price Chopper)",
        "snap_accepted": True,
        "ebt_accepted": False,
        "delivery_fee": 5.99,
        "order_minimum": 10.00,
        "same_day": True,
        "cost_tier": "low",
        "notes": "Fee varies $3.99-$9.99",
    },
    {
        "name": "Dillons/Kroger",
        "snap_accepted": True,
        "ebt_accepted": True,
        "delivery_fee": 9.95,
        "order_minimum": 35.00,
        "same_day": True,
        "cost_tier": "market",
        "notes": "SNAP/EBT accepted",
    },
    {
        "name": "Hy-Vee Aisles Online",
        "snap_accepted": False,
        "ebt_accepted": False,
        "delivery_fee": 9.95,
        "order_minimum": 24.95,
        "same_day": True,
        "cost_tier": "market",
        "notes": "No SNAP/EBT currently",
    },
]


def get_static_delivery_providers() -> list[dict]:
    """Return the 5 hardcoded KC delivery providers with computed weekly total."""
    result: list[dict] = []
    for provider in _STATIC_PROVIDERS:
        p = dict(provider)
        p["estimated_weekly_total"] = round(p["order_minimum"] + p["delivery_fee"], 2)
        if p["snap_accepted"] or p["ebt_accepted"]:
            p["market_rate"] = round(p["delivery_fee"] + p["order_minimum"], 2)
            p["subsidy_applied"] = round(p["delivery_fee"], 2)
            p["final_cost"] = round(p["order_minimum"], 2)
            p["subsidy_label"] = "SNAP/EBT discount applied"
        else:
            p["market_rate"] = round(p["delivery_fee"] + p["order_minimum"], 2)
            p["subsidy_applied"] = 0.0
            p["final_cost"] = round(p["delivery_fee"] + p["order_minimum"], 2)
            p["subsidy_label"] = None
        result.append(p)
    return result


def filter_providers_by_zip(zip_code: str) -> list[dict]:
    """Return providers with serves_zip flag based on KC ZIP prefix (641xx or 661xx)."""
    serves = zip_code.startswith(("641", "661"))
    providers = get_static_delivery_providers()
    for p in providers:
        p["serves_zip"] = serves
    return providers
