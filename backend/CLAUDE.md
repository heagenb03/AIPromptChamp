# Backend CLAUDE.md

## Run

```bash
# First time: create venv and install deps (run from project root)
python -m venv .venv && pip install -r backend/requirements.txt

.venv/Scripts/uvicorn backend.main:app --reload
# or with explicit port:
.venv/Scripts/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
.venv/Scripts/python -m pytest backend/tests/ -v
```

## Environment

- `.env` lives in project root (not `backend/`) — `load_dotenv()` finds it automatically
- `CHALLENGE_API_BASE=https://aipromptchamp.com/api` — real challenge API base URL
- Without it set, all fetchers fall back to mock data silently

## Real API Notes

- All endpoints are under `/api/challenge/...` (e.g. `/api/challenge/pantries`)
- Responses are wrapped: `{ "source": ..., "data": [...] }` — `fetcher.py` unwraps `.data`
- `supply-alerts` uses `{ "status": ..., "alerts": [...] }` — different shape, handled in `cache.py`
- Pantry `type` field uses values like `"food_bank"`, `"shelter_pantry"` — all normalize to `"pantry"`
- Demographics: `povertyRate` is a percent (38.2) not fraction — cache normalizes to 0–1
- Transit: keyed by `nearPantry` pantry ID, not stop ID — `AppCache.pantry_transit[pantry_id]`
- Demographics endpoint only covers KCMO ZIPs (641xx) — KCK ZIPs (66101, 66105, etc.) are absent from the real API; `cache.py:load_all()` supplements hardcoded values from the data brief
- ZIP validation and `filter_providers_by_zip` both accept `641xx` AND `661xx` — do not add 641-only guards

## Cache

All data loaded once at startup via `load_all()`. To reload (e.g. after curveball at 1PM):
**restart the server** — there is no hot-reload of cache data.

## Adding a new endpoint

1. Add fetcher function in `data/fetcher.py` (with mock fallback)
2. Add normalizer + load call in `data/cache.py`
3. Add field to `AppCache` dataclass
4. Use via `AppCache.<field>` in API routes or ML modules

## ML

- `need_score.py` — min-max normalizes 5 features, weighted sum → 0–100 per ZIP
- `produce_routing.py` — `0.4*need_score + 0.3*cold_storage + 0.2*transit_freq + 0.1*lang_es`
- Both run at startup inside `load_all()`, results cached in `AppCache.need_scores`

## Testing

- `tests/conftest.py` has a session-scoped `populated_cache` fixture (autouse) that calls `load_all()` before any test runs — required because `asynccontextmanager` lifespan does NOT fire with bare `TestClient(app)`
- Do not remove or bypass this fixture — tests will pass structurally on an empty cache but return wrong values (need_score=0, options=[], etc.)
- New test files using `TestClient` do not need their own `load_all()` call — conftest handles it

## API Contract

Frozen in `shared/api-contract.md`. Add fields only — never rename or remove.
