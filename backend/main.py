"""
My Compliance Paperwork – FastAPI Application Entry Point
─────────────────────────────────────────────────────────
Run locally:
    cd backend
    uvicorn main:app --reload --port 8000

Interactive API docs:
    http://localhost:8000/docs   (Swagger UI)
    http://localhost:8000/redoc  (ReDoc)
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.routers import analytics, documents, upload
from backend.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=(
        "AI-powered compliance paperwork automation API. "
        "Extracts fields, validates metadata, detects remedial actions, "
        "and routes documents for officer review."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(upload.router)
app.include_router(documents.router)
app.include_router(analytics.router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
def health_check():
    """Returns 200 OK when the service is running."""
    return {"status": "ok", "version": settings.app_version}


logger.info("Application started – %s v%s", settings.app_title, settings.app_version)
