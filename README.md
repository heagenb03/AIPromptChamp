# FoodFlow KC

A desktop web app for Kansas City residents to enter their ZIP code and instantly compare food access options — **free pantries, subsidized delivery, and nearby stores** — ranked by cost and accessibility.

## Quick Start (Frontend)

The frontend requires **no build step**. Open `frontend/index.html` directly in a browser or serve it with any static file server:

```bash
# Option 1 — Python
cd frontend && python3 -m http.server 3000

# Option 2 — Node
cd frontend && npx serve -p 3000
```

Then visit [http://localhost:3000](http://localhost:3000).

### Demo ZIP Codes (mock data)

| ZIP   | Need Score | Produce Alert |
|-------|-----------|---------------|
| 64130 | 82 (High) | Active        |
| 64110 | 65 (Med)  | Inactive      |
| 64108 | 47 (Low)  | Active        |

## Project Structure

```
foodflow-kc/
├── frontend/             # HTML + Tailwind CSS + vanilla JS
│   ├── index.html        # Main page shell
│   ├── css/styles.css    # Custom styles
│   ├── js/
│   │   ├── i18n.js       # EN/ES translation map + toggle
│   │   ├── table.js      # Cost comparison table renderer
│   │   ├── cards.js      # Pantry detail card component
│   │   ├── alerts.js     # Supply alert banner
│   │   └── app.js        # Entry point + orchestration
│   └── assets/
│       └── kc-logo.svg
├── shared/
│   └── api-contract.md   # Frozen API contract
└── README.md
```

## Features

- **ZIP Code Search** — enter a ZIP to see ranked food options
- **Cost Tier Badges** — green (free), amber (low cost), red (market rate)
- **Need Score Badge** — ML-powered 0–100 urgency score per ZIP
- **Pantry Detail Cards** — expandable cards with hours, transit, cold storage
- **Fresh Produce Alert** — bilingual banner when donations are available
- **Spanish Toggle** — one-click EN/ES language switching
- **Community Vote Panel** — demo form for priority neighbourhood voting

## Connecting to the Backend

In `frontend/js/app.js`, set `USE_MOCK = false` and update `API_BASE` to point to the running FastAPI server (default `http://localhost:8000`).
