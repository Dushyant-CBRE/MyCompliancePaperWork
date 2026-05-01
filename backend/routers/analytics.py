"""
Analytics Router  –  GET /api/analytics
─────────────────────────────────────────
Returns aggregated KPI metrics used by the Analytics dashboard.
"""
from __future__ import annotations

from fastapi import APIRouter

from backend.models.document import AnalyticsSummary
from backend.services.storage_service import get_analytics_summary

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsSummary)
def analytics():
    """Return aggregated KPI metrics across all processed documents."""
    return get_analytics_summary()
