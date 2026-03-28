# FoodFlow KC

A hackathon web app for Kansas City residents to instantly compare food access options — free pantries, subsidized delivery, and nearby stores — ranked by cost and accessibility.

**Track:** The Architect | **Hackathon:** AIPromptChamp | **Build Window:** ~4.5 hrs

---

## What It Does

Enter a ZIP code (or describe your location in plain English) and get a ranked list of food options answering: *"How do I get food as cheaply as possible right now?"*

- **3-Path Choice Architecture** — Free pickup / Optimal batched delivery / Instant same-day delivery
- **ML Need Score** — Each ZIP gets a 0–100 urgency score computed from food desert severity, poverty rate, transit access, 311 distress calls, and recent store closures
- **Fresh Produce Alerts** — Live dispatch cards when produce donations are available, with ML-routed drop locations
- **Zero-Surprise Pricing** — Final cost after SNAP/EBT subsidies, no hidden fees
- **Bilingual** — Full EN/ES toggle throughout the UI
- **NLP Input** — "food help near Westside KC" resolves to a ZIP via Claude Haiku

---

## Pages

| Page | Track | Description |
|------|-------|-------------|
| `index.html` | The Architect | Main food finder app |
| `oracle.html` | The Oracle | System pitch dashboard with analytics |
| `Marketing.html` | Marketing | Pitch deck with Overview/Audience/Marketing/Metrics tabs |

All three pages share a nav bar linking between them.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python + FastAPI |
| ML | scikit-learn + numpy |
| Frontend | HTML + Tailwind CSS (CDN) + vanilla JS |
| NLP | Claude Haiku (`claude-haiku-4-5-20251001`) via Anthropic SDK |
| Data | In-memory cache (no database) |

---

## Getting Started

### Prerequisites

- Python 3.10+
- An `ANTHROPIC_API_KEY` (required for NLP ZIP input feature)

### Setup

```bash
# Create and activate virtualenv
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r backend/requirements.txt

# Create .env in project root
echo "CHALLENGE_API_BASE=https://aipromptchamp.com/api" > .env
echo "ANTHROPIC_API_KEY=your_key_here" >> .env
```

### Run

```bash
.venv/Scripts/uvicorn backend.main:app --reload
# or with explicit host/port:
.venv/Scripts/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000` — the FastAPI server serves the frontend as static files.

**Standalone mode:** Open `frontend/index.html` directly in a browser. Built-in mock data fires for ZIPs `64130` (full data), `64110` (no delivery), and `64108` (limited).

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/options?zip=64130` | Ranked food options, need score, alerts, delivery |
| `GET /api/alerts` | Supply alerts and produce routing |
| `POST /api/parse-query` | NLP ZIP extraction from natural language |

### Response Shape (`/api/options`)

```json
{
  "zip": "64130",
  "need_score": 78,
  "need_score_breakdown": {
    "food_desert_severity": 0.82,
    "poverty_rate": 0.91,
    "no_vehicle_pct": 0.74,
    "distress_calls": 0.55,
    "store_closures": 0.40
  },
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
      "cuisine_tags": []
    }
  ],
  "produce_alert": {
    "active": true,
    "pounds": 1000,
    "expires_in_hrs": 48,
    "item": "fresh produce",
    "top_drop_locations": []
  },
  "delivery_necessity_flag": true,
  "delivery_options": [],
  "community_vote": null
}
```

The API contract is frozen — fields are only ever added, never renamed or removed.

---

## Project Structure

```
AIPromptChamp/
├── backend/
│   ├── main.py                  # FastAPI entry point, mounts frontend
│   ├── api/
│   │   ├── options.py           # GET /api/options?zip=
│   │   ├── alerts.py            # GET /api/alerts
│   │   └── parse_query.py       # POST /api/parse-query (Claude Haiku NLP)
│   ├── data/
│   │   ├── fetcher.py           # Challenge API calls
│   │   ├── cache.py             # In-memory cache, loads all data at startup
│   │   ├── delivery_fetcher.py  # KC delivery providers (Walmart, Amazon Fresh, etc.)
│   │   └── cuisine_tags.py      # Pantry → cuisine tag map
│   ├── ml/
│   │   ├── need_score.py        # Feature engineering + weighted scoring (0–100)
│   │   └── produce_routing.py   # Pantry routing: 0.4*need + 0.3*cold + 0.2*transit + 0.1*ES
│   ├── models/
│   │   └── schemas.py           # Pydantic response models
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── index.html               # Main app shell
│   ├── oracle.html              # Oracle track dashboard
│   ├── Marketing.html           # Marketing track pitch deck
│   └── js/
│       ├── app.js               # ZIP input handler, NLP flow, results orchestration
│       ├── table.js             # Cost comparison table
│       ├── paths.js             # 3-path choice architecture cards
│       ├── cards.js             # Expandable pantry "Drop Zone" cards
│       ├── alerts.js            # Produce alert banners + community vote
│       ├── delivery.js          # Delivery options with subsidy breakdown
│       └── i18n.js              # EN/ES translation map + toggle
│
├── shared/
│   └── api-contract.md          # Frozen API shape
│
├── foodflow-kc-spec.md          # Full project spec
├── PLAN.md                      # OptimalEats alignment plan
└── CLAUDE.md                    # AI assistant guidance
```

---

## ML Design

**Need Score** — weighted sum of normalized features (no training at runtime):

| Feature | Weight | Source |
|---------|--------|--------|
| Food desert severity | 30% | `/food-atlas` |
| Poverty rate | 30% | `/demographics` |
| % no-vehicle households | 20% | `/demographics` |
| 311 distress call volume | 10% | `/311-calls` |
| Recent store closures | 10% | `/store-closures` |

**Produce Routing** — scores pantries when a donation is available:
```
score = 0.4 * need_score + 0.3 * cold_storage + 0.2 * transit_freq + 0.1 * lang_es
```

All scores are precomputed at startup and cached in memory.

---

## ZIP Coverage

The app covers Kansas City across two states:
- **KCMO:** `641xx` ZIP codes
- **KCK:** `661xx` ZIP codes (demographics hardcoded from data brief — not in challenge API)

Notable high-need ZIPs: `66101` and `66105` (top 2 by need score).

---

## Running Tests

```bash
.venv/Scripts/python -m pytest backend/tests/ -v
```

---

## Curveball Features

Both curveball requirements (announced 1PM) were pre-planned:

1. **Community Vote** — surfaces top 2 high-need ZIPs (prioritizes Spanish-dominant ZIPs `66101`, `66105`, `64108`); deadline `2026-04-11`
2. **Fresh Produce Dispatch** — `supply-alerts` API activates the produce routing ML; restoring fresh data requires a server restart
