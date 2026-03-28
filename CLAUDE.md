# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: FoodFlow KC

A hackathon project (Track: The Architect) — a desktop web app for Kansas City residents to compare food access options (free pantries, subsidized delivery, stores) ranked by cost and accessibility, with ML-powered need scoring. Full spec in `foodflow-kc-spec.md`.

---

## Commands

### Backend
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run the FastAPI server (serves frontend as static files)
uvicorn backend.main:app --reload

# Run with explicit host/port
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
No build step — plain HTML/CSS/JS with Tailwind via CDN. Open via the FastAPI static file server or directly in a browser.

---

## Architecture

**Strict ownership split:** `backend/` is Person 1 only, `frontend/` is Person 2 only. Never cross ownership boundaries.

### Backend (`backend/`)
- `main.py` — FastAPI app entry point, mounts frontend as static files, enables CORS
- `api/options.py` — `GET /api/options?zip=XXXXX` — core endpoint returning ranked options JSON
- `api/alerts.py` — `GET /api/alerts` — supply alert + produce routing
- `data/fetcher.py` — All external challenge API calls (`/pantries`, `/food-atlas`, `/demographics`, `/311-calls`, `/store-closures`, `/transit`, `/supply-alerts`, `/harvest`)
- `data/cache.py` — In-memory dict cache, loads all API data at startup (no DB)
- `ml/need_score.py` — Feature engineering + weighted scoring → Need Score (0–100) per ZIP
- `ml/produce_routing.py` — Pantry routing for curveball: `0.4*need_score + 0.3*cold_storage + 0.2*transit_freq + 0.1*language_es`
- `models/schemas.py` — Pydantic response models

### Frontend (`frontend/`)
- `index.html` — Main page shell (ZIP input, table, cards, alert banner, language toggle)
- `js/app.js` — Entry point, ZIP input handler
- `js/table.js` — Cost comparison table renderer (cost tiers: free=green, low=yellow, market=red)
- `js/cards.js` — Expandable pantry detail card component
- `js/alerts.js` — Supply/produce alert banner
- `js/i18n.js` — EN/ES translation map + toggle

### API Contract (`shared/api-contract.md`)
Frozen after 10:15AM. The canonical shape:
```json
GET /api/options?zip=64130
{
  "zip": "64130",
  "need_score": 78,
  "options": [{ "name", "type", "cost_tier", "est_cost", "distance_mi",
                "transit_accessible", "languages", "id_required",
                "cold_storage", "hours", "address" }],
  "produce_alert": { "active", "pounds", "expires_in_hrs", "top_drop_locations" }
}
```
**Rule:** Add fields only — never rename or remove fields once frozen.

### ML Design
- No model training at runtime — precomputed weighted sum using scikit-learn/numpy
- Need Score features: food desert severity, poverty rate, % no-vehicle households, 311 distress call volume, recent store closures
- All features normalized 0–1, cache computed scores for all KC ZIPs at startup

### Git Branches
- `p1/backend` — Person 1
- `p2/frontend` — Person 2
- One merge to `main` at lunch sync (12PM)
