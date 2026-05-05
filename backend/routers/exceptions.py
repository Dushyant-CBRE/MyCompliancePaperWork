"""
Exceptions Router  –  GET /api/exceptions
──────────────────────────────────────────
Returns documents requiring attention, mapped to the Exception shape
the frontend expects:
  { id, site, vendor, ppmType, severity, reason, confidence, sla, assignee }
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Query

from backend.models.document import DocumentStatus, RemedialClassification
from backend.services.storage_service import list_documents

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/exceptions", tags=["exceptions"])


def _severity(record) -> str:
    if record.remedial_result:
        clf = record.remedial_result.classification
        if clf == RemedialClassification.REMEDIAL_CRITICAL:
            return "Critical"
        if clf == RemedialClassification.REMEDIAL_MINOR:
            return "High"
    if record.confidence_score:
        score = record.confidence_score.overall_score
        if score < 50:
            return "High"
        if score < 70:
            return "Medium"
    return "Low"


def _reason(record) -> str:
    if record.remedial_result:
        clf = record.remedial_result.classification
        if clf == RemedialClassification.REMEDIAL_CRITICAL:
            return "Critical remedial action required"
        if clf == RemedialClassification.REMEDIAL_MINOR:
            return "Minor remedial issues detected"
    if record.validation_result and record.validation_result.issues:
        return record.validation_result.issues[0]
    if record.confidence_score:
        return f"Low confidence ({record.confidence_score.overall_score:.0f}%)"
    return "Requires manual review"


@router.get("")
def get_exceptions(
    limit: int = Query(50, ge=1, le=200),
):
    """Return documents that need attention, as Exception objects."""
    # Fetch docs in states that require officer action
    exception_statuses = [
        DocumentStatus.MANUAL_REVIEW.value,
        DocumentStatus.REQUIRES_ATTENTION.value,
    ]

    all_records = list_documents(limit=500)
    exceptions: list[dict] = []

    for rec in all_records:
        # Include manual_review, requires_attention, or any doc with remedial findings
        is_exception = (
            rec.status in (DocumentStatus.MANUAL_REVIEW, DocumentStatus.REQUIRES_ATTENTION)
            or (
                rec.remedial_result
                and rec.remedial_result.classification
                in (RemedialClassification.REMEDIAL_CRITICAL, RemedialClassification.REMEDIAL_MINOR)
            )
        )
        if not is_exception:
            continue

        ef = rec.extracted_fields
        cs = rec.confidence_score
        ins = rec.insights

        exceptions.append({
            "id": rec.document_id,
            "site": (ef.site_name or "") if ef else "",
            "vendor": (ef.vendor_name or "") if ef else "",
            "ppmType": (ef.document_type or "") if ef else "",
            "severity": _severity(rec),
            "reason": _reason(rec),
            "confidence": cs.overall_score if cs else 0.0,
            "sla": (ins.sla_remaining or "Unknown") if ins else "Unknown",
            "assignee": rec.override_by or None,
        })

    # Sort: Critical first, then High, Medium, Low
    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    exceptions.sort(key=lambda e: severity_order.get(e["severity"], 4))

    return {"exceptions": exceptions[:limit], "total": len(exceptions)}
