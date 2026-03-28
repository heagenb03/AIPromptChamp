# FoodFlow KC — Project Spec
**Track:** The Architect | **Team Size:** 2 | **Build Window:** ~4.5 hrs (10AM–2:30PM)

---

## 🎯 Concept

A desktop web app for Kansas City residents to enter their ZIP code and instantly compare food access options — **free pantries, subsidized delivery, and nearby stores** — ranked by cost and accessibility. The goal: answer the question *"How do I get food as cheaply as possible right now?"* in under 30 seconds.

---

## 👤 Target User

A food-insecure Kansas City resident who:
- May not have a car (high transit dependence)
- May speak Spanish as a primary language
- Needs food soon, not a research project
- Has limited mobile data / may be on desktop at a library

---

## 🗂️ Core Features

### 1. ZIP Code Entry + Cost Comparison Table
User enters ZIP → app returns a ranked list of options:

| Option | Type | Est. Cost | Distance | Transit? | Language | Notes |
|---|---|---|---|---|---|---|
| Harvester's Food Network | Pantry | **Free** | 1.2 mi | Yes | EN/ES | Open today |
| Walmart Grocery Delivery | Delivery | ~$35+ | — | — | EN | $7.95 delivery fee |
| Price Chopper (64110) | Store | ~$40-60/wk | 2.1 mi | No | EN | Nearest open store |

Cost tiers:
- 🟢 **Free** — food pantries, community fridges
- 🟡 **Low Cost** — SNAP-eligible stores, discount grocers
- 🔴 **Market Rate** — standard delivery, full-price stores

### 2. Pantry Detail Cards
Clicking a pantry option expands:
- Hours, address, language support
- ID requirements (yes/no)
- Cold storage available (relevant for produce curveball)
- Transit bus stops within walking distance

### 3. ML-Powered Need Score Badge
Each ZIP gets a **Need Score (0–100)** displayed as a badge. Computed server-side from a weighted model (see ML section). Used to:
- Surface a "High Need Alert" banner if user's ZIP scores above threshold
- Prioritize pantry options that serve high-need ZIPs

### 4. Fresh Produce Alert Banner (Curveball)
If `supply-alerts` API returns an active donation:
- Full-width banner: *"🥦 1,000 lbs of fresh produce available — pick up at [pantry] before [time]"*
- Bilingual (EN/ES)
- Clicking shows the top 3 pantries recommended for the donation drop (ML routing output)

### 5. Spanish Language Toggle
One-click toggle in the nav: `EN | ES`. Translates:
- UI labels and pantry detail cards
- Alert banners
- Recommendation text

---

## 🧠 ML Component

### Scope Decision
Given the 4.5-hour window, ML is scoped to **lightweight scoring and ranking only** (scikit-learn). No model training during the competition — use pre-computed weights and inference at request time.

### Need Score Model
**Goal:** Produce a 0–100 urgency score per ZIP code.

**Features (all from challenge APIs):**
| Feature | Source Endpoint | Weight |
|---|---|---|
| Food desert severity | `/food-atlas` | High |
| Poverty rate | `/demographics` | High |
| % households with no vehicle | `/demographics` | Medium |
| 311 housing/utility distress call volume | `/311-calls` | Medium |
| # recent grocery store closures within ZIP | `/store-closures` | Medium |

**Model:** `sklearn` `LinearRegression` or manual weighted sum. Normalize each feature 0–1, apply weights, output 0–100 score. Precompute for all KC ZIPs at app startup and cache.

**Output uses:**
1. Need Score badge on user's ZIP
2. Sort/filter pantry recommendations
3. Produce routing: top 3 ZIPs combining high need score + pantry cold storage + transit access

### Pantry Routing (Curveball Logic)
When a produce donation is detected via `supply-alerts`:
```
score(pantry) = 0.4 * need_score(zip)
              + 0.3 * has_cold_storage
              + 0.2 * transit_frequency(nearest_bus_stop)
              + 0.1 * language_match(ES)
```
Return top 3 pantries as recommended drop locations.

### Why Not More?
- Recommendation engine: needs user history data we don't have
- Demand forecasting: needs time-series data; APIs likely don't return historical snapshots
- Clustering: cool but doesn't add direct user value in the frontend — better suited for Oracle track

---

## 🔌 API Usage Map

| Endpoint | Used For |
|---|---|
| `/pantries` | Pantry cards, hours, language, cold storage |
| `/food-atlas` | Food desert score per ZIP (ML feature) |
| `/demographics` | Poverty rate, no-vehicle % (ML features) |
| `/311-calls` | Distress volume per ZIP (ML feature) |
| `/store-closures` | Nearby closure count (ML feature + store list) |
| `/transit` | Bus stop proximity for pantries + routing score |
| `/supply-alerts` | Fresh produce donation banner |
| `/harvest` | After the Harvest priority ZIPs (highlight in UI) |

All endpoints return JSON with CORS enabled. Call from Python backend, cache at startup.

---

## 🏗️ Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Backend | Python + FastAPI | Fast setup, natural for scikit-learn integration |
| ML | scikit-learn + numpy | Lightweight, no GPU needed, familiar |
| Frontend | HTML + Tailwind CSS + vanilla JS | No build step, fast to iterate |
| Map (optional) | Leaflet.js | Free, lightweight, CDN-loadable |
| Data caching | In-memory dict at startup | No DB needed for 4.5hr demo |

---

## 📁 Directory Structure

Folders are split by owner so you never touch the same file. **Person 1 owns `backend/`, Person 2 owns `frontend/`.**

```
foodflow-kc/
│
├── backend/                        # Person 1 — never touched by Person 2
│   ├── main.py                     # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── options.py              # GET /api/options?zip=
│   │   └── alerts.py              # GET /api/alerts (supply + produce)
│   ├── data/
│   │   ├── __init__.py
│   │   ├── fetcher.py              # All challenge API calls
│   │   └── cache.py               # In-memory cache, startup loader
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── need_score.py           # Feature engineering + weighted scoring
│   │   └── produce_routing.py     # Curveball routing logic
│   ├── models/
│   │   └── schemas.py             # Pydantic response models
│   └── requirements.txt
│
├── frontend/                       # Person 2 — never touched by Person 1
│   ├── index.html                  # Main page shell
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   ├── app.js                 # Entry point, ZIP input handler
│   │   ├── table.js               # Cost comparison table renderer
│   │   ├── cards.js               # Pantry detail card component
│   │   ├── alerts.js              # Supply alert banner
│   │   └── i18n.js                # EN/ES translation map + toggle
│   └── assets/
│       └── kc-logo.svg
│
├── shared/
│   └── api-contract.md            # Frozen after 10:15AM — see below
│
├── .gitignore
└── README.md
```

### API Contract (`shared/api-contract.md`)
Define this together at 10AM and **freeze it by 10:15AM**. Person 2 builds against mock JSON matching this shape; Person 1 builds the real endpoint to return it. At lunch sync you swap mock for real.

```json
GET /api/options?zip=64130

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
      "address": "123 Main St"
    }
  ],
  "produce_alert": {
    "active": true,
    "pounds": 1000,
    "expires_in_hrs": 48,
    "top_drop_locations": []
  }
}
```

### Git Rules
1. Branch names: `p1/backend` and `p2/frontend`
2. Never edit files outside your folder
3. One merge to `main` at lunch — not continuous
4. `shared/api-contract.md` is read-only after 10:15AM; changes require verbal agreement
5. If the response shape needs to change: **add fields only, never rename or remove**

---

## 👥 Division of Labor

### Person 1 — Backend + ML
- FastAPI app setup
- API data fetching + caching layer
- Need Score model (feature engineering + weighted scoring)
- Produce routing logic
- `/api/options?zip=XXXXX` endpoint that returns ranked options JSON

### Person 2 — Frontend + UX
- HTML/CSS layout (ZIP entry, comparison table, pantry cards)
- Fetch from backend API + render results
- Spanish toggle (static translation map)
- Supply alert banner
- Polish + demo prep

**Sync point at 12PM (lunch):** Backend should have the `/api/options` endpoint returning real data. Frontend should have the layout rendering mock data. Merge and wire together in Block 2.

---

## 📋 Build Order (Time Budget)

| Time | Person 1 | Person 2 |
|---|---|---|
| 10:00–10:30 | FastAPI scaffolding, fetch + cache all API data | HTML skeleton, ZIP input, mock table |
| 10:30–11:30 | Feature engineering + Need Score model | Pantry card component, cost tier badges |
| 11:30–12:00 | `/api/options` endpoint live | Fetch real data from backend, render |
| 12:00–1:00 | **Lunch + integration** | **Lunch + integration** |
| 1:00–1:30 | Curveball: wire `supply-alerts`, produce routing | Curveball: alert banner + ES translations |
| 1:30–2:15 | Stress test, edge cases (no results, bad ZIP) | Polish, demo script, screenshots |
| 2:15–2:30 | **Submit** | **Submit** |

---

## 🚨 Curveball Response Plan

The curveball is already known:
1. **Community vote requirement** for 2 priority zones — one 80% Spanish-speaking
2. **1,000 lbs fresh produce** expiring in 48 hours

**Response:**
- Spanish toggle already planned → highlight ES-supported pantries prominently in those ZIPs
- Produce routing already built as part of ML component → activate via `supply-alerts` API at 1PM
- Add a "Community Vote" panel below the alert banner with a simple mock form (name, ZIP, support Y/N) — this doesn't need to be real, just demoable

---

## 🏆 Scoring Alignment

| Dimension | How We Address It |
|---|---|
| Problem Understanding | User-centered framing (cheapest food, not logistics), bilingual, transit-aware |
| Solution Quality | Real API data, ML-ranked results, actually usable |
| Presentation & Polish | Clean desktop layout, cost tier color coding, live banner |
| Adaptability | Curveball features baked in from minute one, not bolted on |
| AI Mastery | ML scoring model, AI-assisted Spanish copy, iterative prompt approach for routing weights |

---

## 🔗 Submission Checklist
- [ ] Live demo URL (localhost is fine if screen-sharing during judging)
- [ ] `/api/options?zip=64130` returns ranked results
- [ ] Supply alert banner fires when `supply-alerts` has active data
- [ ] Spanish toggle works on key UI elements
- [ ] Need Score badge visible per ZIP
- [ ] Produce routing shows top 3 pantries with reasoning
