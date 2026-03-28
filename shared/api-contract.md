# FoodFlow KC — API Contract

> **FROZEN after 10:15 AM.** Add fields only — never rename or remove.

---

## GET /api/options?zip=64130

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
      "address": "3801 Topping Ave, Kansas City, MO 64129"
    }
  ],
  "produce_alert": {
    "active": true,
    "pounds": 1000,
    "expires_in_hrs": 48,
    "top_drop_locations": [
      {
        "name": "Harvesters Food Network",
        "address": "3801 Topping Ave, Kansas City, MO 64129",
        "routing_score": 82.4,
        "reason": "High need ZIP, cold storage available, transit-accessible"
      }
    ]
  }
}
```

### Cost Tier Values
- `"free"` — pantries, community fridges
- `"low"` — SNAP-eligible stores, discount grocers
- `"market"` — standard delivery, full-price stores

---

## GET /api/alerts

```json
{
  "active": true,
  "pounds": 1000,
  "expires_in_hrs": 48,
  "item": "fresh produce",
  "top_drop_locations": [
    {
      "name": "Harvesters Food Network",
      "address": "3801 Topping Ave, Kansas City, MO 64129",
      "routing_score": 82.4,
      "reason": "High need ZIP, cold storage available, transit-accessible"
    }
  ]
}
```

---

## POST /api/vote

**Request:**
```json
{
  "name": "Jane Doe",
  "zip": "64130",
  "support": true
}
```

**Response:**
```json
{
  "status": "recorded",
  "message": "Thank you for your vote!"
}
```
