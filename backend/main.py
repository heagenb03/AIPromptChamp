"""FoodFlow KC — FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.alerts import router as alerts_router
from backend.api.options import router as options_router
from backend.data.cache import load_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

_FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — loading all API data...")
    load_all()
    logger.info("Startup complete. FoodFlow KC is ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="FoodFlow KC API",
    description="Food access comparison for Kansas City residents",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(options_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")

# Serve frontend as static files (Person 2's work)
if _FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")
