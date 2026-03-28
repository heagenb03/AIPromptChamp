#!/bin/bash
# FoodFlow KC — Railway deployment start script.
# Installs Python dependencies and launches the FastAPI/Uvicorn server.
# Uses the PORT env var set by Railway (defaults to 8000 for local use).

pip install -r requirements.txt
exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
