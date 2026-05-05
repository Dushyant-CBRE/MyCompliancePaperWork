"""
Dashboard Router  –  GET /api/dashboard
────────────────────────────────────────
Returns a single aggregated payload for the frontend dashboard:
  - KPI counters (total, by status, remedial breakdown)
  - Average confidence score
  - Overdue document count
  - 10 most recently uploaded documents
  - Documents currently requiring officer attention

All data is loaded live from Azure Table Storage using the credentials
configured in .env (AZURE_STORAGE_CONNECTION_STRING / AZURE_TABLE_NAME).
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Query

from backend.models.document import (
    DashboardDocumentSummary,
    DashboardResponse,
    DocumentStatus,
    RemedialClassification,
)
from backend.services.storage_service import list_documents

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _to_summary(rec) -> DashboardDocumentSummary:
    """Convert a full DocumentRecord into the lightweight dashboard summary."""
    ef = rec.extracted_fields
    cs = rec.confidence_score
    rr = rec.remedial_result
    ins = rec.insights

    return DashboardDocumentSummary(
        document_id=rec.document_id,
        filename=rec.filename,
        status=rec.status,
        site_name=ef.site_name if ef else None,
        document_type=ef.document_type if ef else None,
        inspection_date=ef.inspection_date if ef else None,
        next_service_date=ef.next_service_date if ef else None,
        overall_confidence=round(cs.overall_score, 2) if cs else None,
        remedial_classification=rr.classification.value if rr else None,
        compliance_status=ins.compliance_status if ins else None,
        risk_level=ins.risk_level if ins else None,
        is_overdue=ins.is_overdue if ins else False,
        uploaded_at=rec.uploaded_at,
        processed_at=rec.processed_at,
    )


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    limit: int = Query(
        200,
        ge=1,
        le=1000,
        description="Maximum number of documents to fetch from Azure Table for aggregation",
    ),
    recent: int = Query(
        10, ge=1, le=50, description="Number of recent documents to include in the feed"
    ),
):
    """
    Aggregated dashboard data loaded directly from Azure Table Storage.

    Uses credentials from AZURE_STORAGE_CONNECTION_STRING and
    AZURE_TABLE_NAME in .env.
    """
    records = list_documents(limit=limit)

    response = DashboardResponse(total_documents=len(records))

    confidence_sum = 0.0
    confidence_count = 0

    _attention_statuses = {
        DocumentStatus.MANUAL_REVIEW,
        DocumentStatus.REQUIRES_ATTENTION,
    }

    attention_docs: list[DashboardDocumentSummary] = []

    for rec in records:
        # ── Status counters ───────────────────────────────────────────────────
        s = rec.status
        if s == DocumentStatus.PENDING:
            response.pending += 1
        elif s == DocumentStatus.PROCESSING:
            response.processing += 1
        elif s == DocumentStatus.AUTO_APPROVED:
            response.auto_approved += 1
        elif s == DocumentStatus.MANUAL_REVIEW:
            response.manual_review += 1
        elif s == DocumentStatus.REQUIRES_ATTENTION:
            response.requires_attention += 1
        elif s == DocumentStatus.APPROVED:
            response.approved += 1
        elif s == DocumentStatus.REJECTED:
            response.rejected += 1

        # ── Confidence ────────────────────────────────────────────────────────
        if rec.confidence_score:
            confidence_sum += rec.confidence_score.overall_score
            confidence_count += 1

        # ── Remedial breakdown ────────────────────────────────────────────────
        if rec.remedial_result:
            clf = rec.remedial_result.classification
            if clf == RemedialClassification.PASS:
                response.remedial_pass += 1
            elif clf == RemedialClassification.REMEDIAL_MINOR:
                response.remedial_minor += 1
            elif clf == RemedialClassification.REMEDIAL_CRITICAL:
                response.remedial_critical += 1

        # ── Overdue count ─────────────────────────────────────────────────────
        if rec.insights and rec.insights.is_overdue:
            response.overdue_count += 1

        # ── Attention feed (manual_review / requires_attention) ───────────────
        if s in _attention_statuses:
            attention_docs.append(_to_summary(rec))

    # ── Average confidence ────────────────────────────────────────────────────
    if confidence_count:
        response.avg_confidence = round(confidence_sum / confidence_count, 2)

    # ── Recent documents feed (already sorted newest-first by list_documents) ─
    response.recent_documents = [_to_summary(r) for r in records[:recent]]

    # Sort attention docs by uploaded_at descending; surface newest first
    attention_docs.sort(key=lambda d: d.uploaded_at, reverse=True)
    response.attention_documents = attention_docs

    logger.info(
        "Dashboard built: total=%d attention=%d overdue=%d",
        response.total_documents,
        len(response.attention_documents),
        response.overdue_count,
    )
    return response
