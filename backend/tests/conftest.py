"""
Shared pytest configuration.

The FastAPI app uses an asynccontextmanager lifespan. The bare TestClient()
pattern does not trigger the lifespan, so AppCache is empty during requests
unless we seed it explicitly.

This session-scoped fixture calls load_all() once before any test runs,
matching exactly what the production startup does.
"""
from __future__ import annotations

import pytest

from backend.data.cache import load_all


@pytest.fixture(scope="session", autouse=True)
def populated_cache():
    """Populate AppCache before any test runs. Session scope — runs once."""
    load_all()
