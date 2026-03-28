# FoodFlow KC — Build Plan (Person 1: Backend + ML)

**Hackathon Window:** 10:00 AM – 2:30 PM (4.5 hrs)
**Today:** 2026-03-28

---

## Phase 1 — Scaffold + Data Layer (10:00–10:30)

**Goal:** FastAPI running, all external API data loading at startup into memory cache.

### Tasks
- [x] Create `backend/` directory structure
- [ ] `backend/requirements.txt` — pin dependencies
- [ ] `backend/main.py` — FastAPI app, CORS, static file mount, startup event
- [ ] `backend/data/fetcher.py` — HTTP calls to all 8 challenge endpoints
- [ ] `backend/data/cache.py` — in-memory dict, `load_all()` called at startup
- [ ] `backend/models/schemas.py` — Pydantic models for API responses

**Checkpoint:** `uvicorn backend.main:app --reload` starts without errors, `/docs` loads.

---

## Phase 2 — ML: Need Score Model (10:30–11:30)

**Goal:** `need_score(zip) → int 0–100` working for all KC ZIPs.

### Tasks
- [ ] `backend/ml/need_score.py`
  - Pull 5 features per ZIP from cache (food atlas, demographics, 311, store closures)
  - Normalize each feature 0–1 with min-max scaling
  - Weighted sum → 0–100 score
  - Cache results in `AppCache.need_scores` at startup
- [ ] Unit test: spot-check 3 ZIPs produce expected range

**Checkpoint:** `from ml.need_score import compute_all_scores` runs and returns dict of ZIP → score.

---

## Phase 3 — Core API Endpoint (11:30–12:00)

**Goal:** `GET /api/options?zip=64130` returns fully ranked options JSON per the API contract.

### Tasks
- [ ] `backend/api/options.py`
  - Validate ZIP (KC range: 641xx–641xx)
  - Pull pantries + stores within distance threshold
  - Attach transit accessibility from `/transit` cache
  - Sort: free first → low-cost → market rate; secondary sort by distance
  - Attach `need_score` and `produce_alert` (initially `active: false`)
- [ ] Wire into `main.py` router

**Checkpoint:** `curl "http://localhost:8000/api/options?zip=64130"` returns valid JSON matching `shared/api-contract.md`.

---

## Phase 4 — Lunch + Integration Sync (12:00–1:00)

**Goal:** Merge `p1/backend` → `main`, wire backend to frontend mock.

### Tasks
- [ ] Git commit all backend work
- [ ] Merge to `main`
- [ ] Verify frontend's `fetch('/api/options?zip=...')` returns real data
- [ ] Fix any CORS or shape mismatches

---

## Phase 5 — Curveball: Produce Routing (1:00–1:30)

**Goal:** `GET /api/alerts` returns active produce donation with top-3 pantry routing.

### Tasks
- [ ] `backend/ml/produce_routing.py`
  - Score pantries: `0.4*need_score + 0.3*cold_storage + 0.2*transit_freq + 0.1*lang_es`
  - Return top 3 pantries as `top_drop_locations`
- [ ] `backend/api/alerts.py`
  - Poll `supply-alerts` endpoint (already in cache)
  - If active: run routing, return banner data
- [ ] Wire into `main.py` router

**Checkpoint:** `curl http://localhost:8000/api/alerts` returns `{ active: true, top_drop_locations: [...] }`.

---

## Phase 6 — Hardening + Edge Cases (1:30–2:15)

### Tasks
- [ ] Bad ZIP → 404 with clear message
- [ ] Empty results (no pantries nearby) → empty array, not crash
- [ ] API fetch failure → log and return cached/fallback data
- [ ] Add `POST /api/vote` stub for community vote curveball (returns 200 + mock confirmation)
- [ ] Smoke test all endpoints

---

## Phase 7 — Submit (2:15–2:30)

- [ ] Final commit on `main`
- [ ] Verify `http://localhost:8000` serves the full app
- [ ] Demo run: enter ZIP 64130, see ranked results, see produce alert, toggle ES

---

## API Contract Reference

```
GET /api/options?zip=64130
GET /api/alerts
POST /api/vote  (curveball stub)
```

Full contract shape in `shared/api-contract.md`.

---

## KC ZIP Codes to Support

Primary test ZIPs:
- `64130` — high food insecurity area
- `64110` — mid KC
- `64108` — downtown KC
- `64114` — south KC
- `64151` — north KC

---

## Challenge Endpoints (External APIs)

| Endpoint | Data | Cache Key |
|---|---|---|
| `/pantries` | Pantry list, hours, lang, cold storage | `pantries` |
| `/food-atlas` | Food desert severity per ZIP | `food_atlas` |
| `/demographics` | Poverty rate, no-vehicle % per ZIP | `demographics` |
| `/311-calls` | Distress call volume per ZIP | `calls_311` |
| `/store-closures` | Recent closures per ZIP | `store_closures` |
| `/transit` | Bus stop proximity per location | `transit` |
| `/supply-alerts` | Active produce donations | `supply_alerts` |
| `/harvest` | After the Harvest priority ZIPs | `harvest` |
