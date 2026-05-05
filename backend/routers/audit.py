"""
Audit Router  –  GET /api/audit
────────────────────────────────
Builds an audit log from stored DocumentRecord history:
  - AI decisions (auto_approved, manual_review, requires_attention)
  - Officer overrides (approved / rejected)
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Query

from backend.models.document import DocumentStatus
from backend.services.storage_service import list_documents

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["audit"])


def _build_entries(limit: int) -> list[dict]:
    records = list_documents(limit=limit)
    entries: list[dict] = []

    for rec in records:
        doc_name = rec.filename

        # ── AI decision entry ──────────────────────────────────────────────
        if rec.processed_at and rec.status not in (
            DocumentStatus.PENDING, DocumentStatus.PROCESSING
        ):
            confidence = (
                rec.confidence_score.overall_score if rec.confidence_score else 0.0
            )
            status_label = rec.status.value.replace("_", " ").title()
            entries.append({
                "id": f"{rec.document_id}-ai",
                "timestamp": rec.processed_at.isoformat(),
                "user": "System (AI)",
                "action": status_label,
                "document": doc_name,
                "details": (
                    f"Confidence: {confidence:.1f}%. "
                    + (
                        f"Remedial: {rec.remedial_result.classification.value}"
                        if rec.remedial_result else ""
                    )
                ),
                "reason": None,
                "trainingFeedback": False,
            })

        # ── Officer override entry ─────────────────────────────────────────
        if rec.overridden_at and rec.override_by:
            entries.append({
                "id": f"{rec.document_id}-override",
                "timestamp": rec.overridden_at.isoformat(),
                "user": rec.override_by,
                "action": rec.status.value.replace("_", " ").title(),
                "document": doc_name,
                "details": (
                    f"Changed status to '{rec.status.value}'. "
                    f"Reason: {rec.override_reason or 'Not specified'}"
                ),
                "reason": rec.override_reason,
                "trainingFeedback": False,
            })

    # Sort by timestamp descending
    entries.sort(key=lambda e: e["timestamp"], reverse=True)
    return entries


@router.get("")
def get_audit_log(
    limit: int = Query(100, ge=1, le=500),
):
    """Return audit log entries built from stored document history."""
    entries = _build_entries(limit)
    return {"entries": entries, "total": len(entries)}
