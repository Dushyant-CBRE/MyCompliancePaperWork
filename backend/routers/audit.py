"""
Audit Router  –  GET /api/audit
────────────────────────────────
Returns audit log entries from the MyPaperComplianceAudit Azure Table.
Falls back to dynamically building entries from document records when the
persistent table is empty (e.g. first run before any overrides have been made).

Columns stored per entry:
  timestamp   – UTC ISO datetime of the action
  user        – officer name or "System (AI)"
  status      – new document status value
  document    – filename
  details     – override reason / AI decision summary
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Query

from backend.models.document import AuditLogEntry, AuditLogResponse, DocumentStatus
from backend.services.storage_service import list_audit_logs, list_documents

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["audit"])


def _build_entries_from_docs(limit: int) -> list[AuditLogEntry]:
    """Fallback: build audit entries dynamically from DocumentRecords."""
    from datetime import datetime

    records = list_documents(limit=limit)
    entries: list[AuditLogEntry] = []

    for rec in records:
        # ── AI decision entry ──────────────────────────────────────────────
        if rec.processed_at and rec.status not in (
            DocumentStatus.PENDING, DocumentStatus.PROCESSING
        ):
            confidence = (
                rec.confidence_score.overall_score if rec.confidence_score else 0.0
            )
            remedial_suffix = (
                f" | Remedial: {rec.remedial_result.classification.value}"
                if rec.remedial_result else ""
            )
            entries.append(AuditLogEntry(
                entry_id=f"{rec.document_id}-ai",
                timestamp=rec.processed_at,
                user="System (AI)",
                status=rec.status.value,
                document=rec.filename,
                document_id=rec.document_id,
                details=f"Confidence: {confidence:.1f}%{remedial_suffix}",
            ))

        # ── Officer override entry ─────────────────────────────────────────
        if rec.overridden_at and rec.override_by:
            entries.append(AuditLogEntry(
                entry_id=f"{rec.document_id}-override",
                timestamp=rec.overridden_at,
                user=rec.override_by,
                status=rec.status.value,
                document=rec.filename,
                document_id=rec.document_id,
                details=rec.override_reason or "",
            ))

    entries.sort(key=lambda e: e.timestamp, reverse=True)
    return entries[:limit]


@router.get("", response_model=AuditLogResponse)
def get_audit_log(
    limit: int = Query(100, ge=1, le=500),
    document_id: Optional[str] = Query(None, description="Filter by document ID"),
):
    """
    Return audit log entries from MyPaperComplianceAudit table.
    Falls back to document-derived entries when the table is empty.
    """
    entries = list_audit_logs(document_id=document_id, limit=limit)

    # If no persistent entries yet, build from document records as fallback
    if not entries and not document_id:
        entries = _build_entries_from_docs(limit)

    return AuditLogResponse(entries=entries, total=len(entries))

