# FoodFlow KC — API Contract

> **Status:** FROZEN — changes require verbal agreement between Person 1 & Person 2.
> Only *additive* changes (new fields) are permitted; never rename or remove.

---

## `GET /api/options?zip={ZIP}`

Returns ranked food access options for a Kansas City ZIP code, including
a Need Score and any active produce alerts.

### Response Shape

```json
{
  "zip": "64130",
  "need_score": 78,
  "options": [
    {
      "name": "Harvesters Food Network",
      "type": "pantry",
      "cost_tier": "free",
      "est_cost": "$0",
      "distance_mi": 1.2,
      "transit_accessible": true,
      "languages": ["en", "es"],
      "id_required": false,
      "cold_storage": true,
      "hours": "Mon-Fri 9AM-5PM",
      "address": "123 Main St",
      "notes": "Open today"
    }
  ],
  "produce_alert": {
    "active": true,
    "pounds": 1000,
    "expires_in_hrs": 48,
    "top_drop_locations": [
      {
        "name": "Harvesters Food Network",
        "address": "3801 Topping Ave"
      }
    ]
  }
}
```

### Field Reference

| Field | Type | Description |
|---|---|---|
| `zip` | string | The queried 5-digit ZIP code |
| `need_score` | int (0-100) | ML-computed urgency score for the ZIP |
| `options` | array | Ranked list of food access options |
| `options[].name` | string | Display name of the option |
| `options[].type` | enum | `"pantry"` \| `"delivery"` \| `"store"` |
| `options[].cost_tier` | enum | `"free"` \| `"low"` \| `"market"` |
| `options[].est_cost` | string | Human-readable cost estimate |
| `options[].distance_mi` | float \| null | Distance in miles (null for delivery) |
| `options[].transit_accessible` | bool \| null | Bus stop within walking distance |
| `options[].languages` | string[] | Supported languages (`"en"`, `"es"`) |
| `options[].id_required` | bool | Whether photo ID is needed |
| `options[].cold_storage` | bool \| null | Refrigeration for produce |
| `options[].hours` | string | Operating hours |
| `options[].address` | string \| null | Physical address (null for delivery) |
| `options[].notes` | string | Additional info |
| `produce_alert` | object | Fresh produce donation alert |
| `produce_alert.active` | bool | Whether an alert is currently active |
| `produce_alert.pounds` | int | Pounds of produce available |
| `produce_alert.expires_in_hrs` | int | Hours until expiration |
| `produce_alert.top_drop_locations` | array | ML-routed top 3 pantries for drop-off |

### Error Response

```json
{ "detail": "No data available for ZIP 99999" }
```

HTTP 404 with the above body.
