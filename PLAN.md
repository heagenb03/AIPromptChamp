# FoodFlow KC → OptimalEats Alignment Plan

This plan upgrades FoodFlow KC to align with the OptimalEats vision from the Gemini
conversations. All changes stay within **The Architect** track scope: a working tool
judges can interact with.

The guiding principle is **reframe first, add second** — existing backend data is
sufficient for most changes. Only Phase 3 requires a new external dependency.

---

## Context: What OptimalEats Is

OptimalEats (from the Gemini sources in the NotebookLM notebook "OptimalEats KC AI
Event") is an "Invisible AI" food logistics aggregator that hides complexity behind
a radically simple interface. Its core pitch to judges is:

1. **Choice Architecture** — a 3-path comparison: Free pickup / Optimal batched
   delivery / Instant standard delivery
2. **Zero-Surprise Pricing** — show the final cost after subsidies, no hidden fees
3. **Neighborhood Drop Zones** — reframe pantries as community pickup hubs
4. **Active Dispatch Language** — when produce is available, it's a live routing
   event, not a passive banner
5. **Unit Economics Dashboard** — judges see the algorithm's reasoning, not just results
6. **NLP Input** — "I need groceries in 64130" instead of a raw ZIP box

FoodFlow KC already has all the data to support items 1–5. Item 6 requires one new
endpoint using the Claude API.

---

## Current Architecture (do not break these)

### Backend
- `backend/main.py` — FastAPI app, mounts frontend as static files
- `backend/api/options.py` — `GET /api/options?zip=XXXXX` — core endpoint
- `backend/api/alerts.py` — `GET /api/alerts` — supply alert + produce routing
- `backend/data/fetcher.py` — challenge API calls
- `backend/data/cache.py` — in-memory cache, loads all data at startup via `load_all()`
- `backend/ml/need_score.py` — weighted sum need score (0–100) per ZIP
- `backend/ml/produce_routing.py` — pantry routing score formula
- `backend/models/schemas.py` — Pydantic response models

### Frontend
- `frontend/index.html` — shell: ZIP input, table, cards, alert banner, language toggle
- `frontend/js/app.js` — ZIP input handler, calls `/api/options`
- `frontend/js/table.js` — renders the cost comparison table
- `frontend/js/cards.js` — expandable pantry detail cards
- `frontend/js/alerts.js` — supply/produce alert banner
- `frontend/js/i18n.js` — EN/ES translation map + toggle
- `frontend/js/delivery.js` — delivery options section

### API Contract Rules
- File: `shared/api-contract.md`
- **FROZEN**: add fields only — never rename or remove existing fields
- Valid ZIP prefixes: `641xx` (KCMO) and `661xx` (KCK) — both must always work
- KCK demographics are hardcoded in `cache.py` (not in the challenge API)

### Need Score Features & Weights (from `ml/need_score.py`)
```
food_desert_severity  weight: 0.30  source: AppCache.food_atlas[zip]
poverty_rate          weight: 0.30  source: AppCache.demographics[zip]["poverty_rate"]
no_vehicle_pct        weight: 0.20  source: AppCache.demographics[zip]["no_vehicle_pct"]
distress_calls        weight: 0.10  source: AppCache.calls_311[zip]
store_closures        weight: 0.10  source: AppCache.store_closures[zip]
```

### Produce Routing Formula (from `ml/produce_routing.py`)
```
score = 0.4*need_score + 0.3*cold_storage + 0.2*transit_freq + 0.1*lang_es
```

### Key Schema Fields (from `models/schemas.py`)
```python
FoodOption:     name, type, cost_tier, est_cost, distance_mi, transit_accessible,
                languages, id_required, cold_storage, hours, address, cuisine_tags

DeliveryOption: name, snap_accepted, ebt_accepted, delivery_fee, order_minimum,
                estimated_weekly_total, same_day, cost_tier, serves_zip, notes

OptionsResponse: zip, need_score, options, produce_alert,
                 delivery_necessity_flag, delivery_options

ProduceAlert:   active, pounds, expires_in_hrs, item, top_drop_locations
DropLocation:   name, address, routing_score, reason
```

---

## Phase 1 — UI Reframe (Frontend Only, No Backend Changes)

**Goal:** Restructure results into the OptimalEats Choice Architecture. Same data,
dramatically better framing for judges.

### 1A. Choice Architecture — 3-Path Results Screen

Replace the flat ranked table in `frontend/js/table.js` with a 3-column or
3-card layout:

| Path | Label | Source Data | Visual Treatment |
|------|-------|-------------|-----------------|
| A | Free Route | `cost_tier === "free"` options (pantries) | Green — "No cost" |
| B | Optimal Route | Cheapest `delivery_options` entry | Yellow — "Best value" |
| C | Instant Route | `same_day === true` delivery options | Blue — "Get it today" |

**Rules:**
- "Optimal Route" is the delivery option with the lowest `estimated_weekly_total`
  where `serves_zip === true`
- "Instant Route" is the cheapest `same_day === true` delivery option
- If no delivery options exist, collapse B and C with a "Not available in your ZIP"
  message
- The existing detailed table/cards should still render below the 3-path header as
  supporting detail — do not remove it
- Add EN/ES translations to `frontend/js/i18n.js` for all new labels

**New i18n keys needed:**
```js
"free_route_label":    "Free Route" / "Ruta Gratuita"
"optimal_route_label": "Optimal Route" / "Ruta Óptima"
"instant_route_label": "Instant Route" / "Entrega Inmediata"
"best_value_badge":    "Best Value" / "Mejor Precio"
"no_delivery_zip":     "Delivery not available in your area" / "Entrega no disponible en su área"
```

### 1B. Drop Zone Reframing

In `frontend/js/cards.js`, rename pantry cards to "Drop Zones" and add badges:

- If `cold_storage === true` → show "Cold Storage" badge
- If `transit_accessible === true` → show "Transit Access" badge
- If `id_required === false` → show "No ID Required" badge
- Display languages as pills (EN, ES, etc.)

Do NOT change backend field names — this is presentation only.

**New i18n keys needed:**
```js
"drop_zone_label":    "Drop Zone" / "Zona de Entrega"
"cold_storage_badge": "Cold Storage" / "Almacenamiento Frío"
"transit_badge":      "Transit Access" / "Acceso en Tránsito"
"no_id_badge":        "No ID Required" / "Sin Identificación"
```

### 1C. Produce Alert → Active Drop Mission

In `frontend/js/alerts.js`, when `produce_alert.active === true`, replace the
static banner with a live-dispatch card:

```
ACTIVE DROP MISSION
[item] — [pounds] lbs available — expires in [expires_in_hrs] hrs
Routing to [top_drop_locations[0].name], [top_drop_locations[1].name],
[top_drop_locations[2].name]
[reason text from routing_score]
```

Show a countdown-style urgency indicator based on `expires_in_hrs`:
- ≤ 12 hrs → red "URGENT"
- 13–24 hrs → orange "TODAY"
- > 24 hrs → yellow "ACTIVE"

**New i18n keys needed:**
```js
"active_mission_label": "Active Drop Mission" / "Misión de Entrega Activa"
"routing_to_label":     "Routing to" / "Enviando a"
"urgent_label":         "URGENT" / "URGENTE"
"today_label":          "TODAY" / "HOY"
```

---

## Phase 2 — Backend Enhancements (New Fields, Additive Only)

**Goal:** Expose the algorithm's reasoning and add subsidy visualization.
All changes are additive — no existing fields are renamed or removed.

### 2A. Need Score Breakdown Field

**File:** `backend/models/schemas.py` — add to `OptionsResponse`:
```python
need_score_breakdown: dict[str, float] = Field(default_factory=dict)
```

The breakdown should look like:
```json
{
  "food_desert_severity": 0.82,
  "poverty_rate": 0.91,
  "no_vehicle_pct": 0.74,
  "distress_calls": 0.55,
  "store_closures": 0.40
}
```
These are the **normalized** (0–1) feature values for the queried ZIP, not the
raw values. They represent each factor's contribution before weighting.

**File:** `backend/ml/need_score.py` — add a new function:
```python
def get_score_breakdown(zip_code: str) -> dict[str, float]:
    """
    Returns normalized feature values (0–1) for a single ZIP.
    Used for judge-facing transparency panel.
    """
```
This function should look up raw values from `AppCache` for the given ZIP,
normalize them using the global min/max already computed in `compute_all_scores()`,
and return them as a dict. Consider caching the min/max values alongside scores
in `AppCache` so `get_score_breakdown()` can reuse them without recomputing.

**File:** `backend/api/options.py` — call `get_score_breakdown(zip)` and include
it in the `OptionsResponse`.

**File:** `frontend/js/app.js` or a new `frontend/js/breakdown.js` — render a
collapsible "Why this score?" panel below the need score display, showing each
factor as a labeled progress bar (0–100% of max). Label the bars in plain language:

```
Food Desert Severity  ████████░░  82%
Poverty Rate          █████████░  91%
No Vehicle Access     ████████░░  74%
Distress Calls (311)  ██████░░░░  55%
Recent Store Closures ████░░░░░░  40%
```

Add EN/ES i18n keys for each label.

### 2B. Subsidy Visualization on Delivery Options

**File:** `backend/models/schemas.py` — add to `DeliveryOption`:
```python
market_rate: float | None = None          # original cost before subsidy
subsidy_applied: float | None = None      # dollar amount knocked off
final_cost: float | None = None           # what user actually pays
subsidy_label: str | None = None          # e.g. "SNAP discount", "EBT accepted"
```

**File:** `backend/data/delivery_fetcher.py` — compute these fields when building
delivery provider records. Logic:
- If `snap_accepted or ebt_accepted`:
  - `market_rate = delivery_fee + order_minimum` (approximate)
  - `subsidy_applied = delivery_fee` (delivery fee waived for SNAP users — this is
    the OptimalEats "Zero-Surprise Pricing" model; adjust if actual rules differ)
  - `final_cost = order_minimum`
  - `subsidy_label = "SNAP/EBT discount applied"`
- Otherwise:
  - `market_rate = delivery_fee + order_minimum`
  - `subsidy_applied = 0.0`
  - `final_cost = market_rate`
  - `subsidy_label = None`

**File:** `frontend/js/delivery.js` — when rendering a delivery option that has
`subsidy_applied > 0`, show the breakdown:
```
Standard cost: $X.XX
SNAP/EBT discount: -$Y.YY
────────────────────
Your cost: $Z.ZZ
```

This directly mirrors the OptimalEats "Subsidy Visualization" pitch and is one of
the most compelling judge-facing features.

---

## Phase 3 — NLP ZIP Input (New Claude API Endpoint)

**Goal:** Replace the raw ZIP input box with a natural language field that lets
users type "I need groceries near 64130" or "food help in Westside KC" and have
the AI resolve it to a valid KC ZIP code.

This is the highest-value AI demo feature — it directly scores on "AI Mastery"
in the judging rubric.

### 3A. Backend — New Parse Query Endpoint

**New file:** `backend/api/parse_query.py`

```python
POST /api/parse-query
Body: { "query": "I need groceries in Westside KC" }
Response: { "zip": "64108", "confidence": "high", "interpreted_as": "Westside Kansas City, MO" }
```

Use the Anthropic Python SDK with `claude-haiku-4-5-20251001` (fastest, cheapest).
System prompt should:
1. Know that valid KC ZIPs are `641xx` (KCMO) and `661xx` (KCK)
2. Extract or infer a ZIP from neighborhood names, landmarks, or explicit ZIPs
3. Return JSON only — no prose
4. If no KC ZIP can be inferred, return `{ "zip": null, "error": "Could not determine a KC ZIP from your input" }`

**Environment variable needed:** `ANTHROPIC_API_KEY` in `.env` (project root).
Install: `pip install anthropic` and add `anthropic` to `backend/requirements.txt`.

**Register the router in `backend/main.py`** alongside the existing options and
alerts routers.

**Pydantic schemas to add in `backend/models/schemas.py`:**
```python
class ParseQueryRequest(BaseModel):
    query: str

class ParseQueryResponse(BaseModel):
    zip: str | None
    confidence: Literal["high", "low"] | None = None
    interpreted_as: str | None = None
    error: str | None = None
```

### 3B. Frontend — NLP Input Field

**File:** `frontend/js/app.js` — change the input handler:

1. The input box becomes a text field with placeholder:
   `"Enter ZIP or describe your location (e.g. 'food help near 64130')"` / ES equivalent
2. On submit:
   - If input is exactly 5 digits starting with 641 or 661 → use directly (existing path)
   - Otherwise → `POST /api/parse-query` with the raw text, extract `zip` from response
   - If `zip` is null → show error message from response
   - If `zip` is returned → proceed with `GET /api/options?zip=...` as normal
3. While the NLP request is in flight → show a brief "Interpreting your request..."
   loading state

**File:** `frontend/index.html` — update input placeholder and submit button label.

**New i18n keys needed:**
```js
"input_placeholder":    "Enter ZIP or describe your area" / "Ingrese ZIP o describa su área"
"interpreting_label":   "Interpreting your request..." / "Interpretando su solicitud..."
"nlp_error_label":      "Could not find a KC location. Try a ZIP code." / "No se pudo encontrar una ubicación en KC. Intente con un código ZIP."
```

---

## Phase Order & Dependencies

```
Phase 1 (UI Reframe)
  └── No backend dependency — can start immediately
  └── 1A, 1B, 1C are independent — can be done in any order

Phase 2 (Backend Enhancements)
  └── 2A (need_score_breakdown) — no external deps, start after Phase 1
  └── 2B (subsidy visualization) — no external deps, independent of 2A

Phase 3 (NLP Input)
  └── Requires ANTHROPIC_API_KEY in .env
  └── Requires `pip install anthropic`
  └── Backend (3A) must be done before Frontend (3B)
  └── Can be started in parallel with Phase 2
```

---

## Testing Notes

- Run backend tests after any Python change: `.venv/Scripts/python -m pytest backend/tests/ -v`
- The `conftest.py` `populated_cache` fixture fires `load_all()` before tests — do not bypass it
- New endpoints need test coverage in `backend/tests/`
- For Phase 3, mock the Anthropic API call in tests — do not make real API calls in CI
- ZIP 64130 is a good test ZIP (has full data, high need score)
- ZIP 66101 is KCK test ZIP (hardcoded demographics, verify it still works after any cache changes)

---

## What NOT to Do

- Do not rename or remove any existing API fields (contract is frozen)
- Do not add a database — in-memory cache only
- Do not add a build step to the frontend — plain HTML/CSS/JS with Tailwind CDN only
- Do not change the 641xx/661xx ZIP validation logic
- Do not cross the backend/frontend ownership boundary (backend = Person 1, frontend = Person 2)
- Do not use `claude-opus-4-6` for the NLP endpoint — Haiku is sufficient and much faster
