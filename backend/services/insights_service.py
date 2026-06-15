"""
Insights Generator
───────────────────
Derives high-level DocumentInsights from the three agent outputs
and the extracted fields.  No LLM call — purely deterministic.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from backend.models.document import (
    ConfidenceScore,
    DocumentInsights,
    ExtractedFields,
    RemedialClassification,
    RemedialResult,
    ValidationResult,
)

# All field names we expect to find
_EXPECTED_FIELDS = [
    "site_name", "ppm_reference", "inspection_date", "inspector_name",
    "equipment_id", "document_type", "vendor_name",
    "certificate_number", "next_service_date",
]


def _days_until(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    try:
        target = datetime.fromisoformat(date_str).date()
        return (target - date.today()).days
    except ValueError:
        return None


def _risk_level(remedial: RemedialResult, overall_score: float) -> str:
    if remedial.classification == RemedialClassification.REMEDIAL_CRITICAL:
        return "Critical"
    if remedial.classification == RemedialClassification.REMEDIAL_MINOR:
        return "High" if overall_score < 70 else "Medium"
    if overall_score >= 85:
        return "Low"
    if overall_score >= 60:
        return "Medium"
    return "High"


def _compliance_status(remedial: RemedialResult, validation: ValidationResult) -> str:
    # Simplified policy: compliance is determined by remedial findings, but only
    # when there is actual supporting evidence/items. If the remedial agent
    # returned a classification but provided no findings/evidence, treat as
    # Compliant to avoid false-positive UI labels.
    has_evidence = bool(
        (remedial.evidence and len(remedial.evidence) > 0)
        or (remedial.critical_items and len(remedial.critical_items) > 0)
        or (remedial.minor_items and len(remedial.minor_items) > 0)
        or (remedial.findings and len(remedial.findings) > 0)
    )

    if remedial.classification == RemedialClassification.REMEDIAL_CRITICAL and has_evidence:
        return "Non-Compliant"
    if remedial.classification == RemedialClassification.REMEDIAL_MINOR and has_evidence:
        return "Remedial Action Required"
    return "Compliant"


def _sla_remaining(days: Optional[int]) -> Optional[str]:
    """Convert days_until_next_service into a human-readable SLA string."""
    if days is None:
        return None
    if days < 0:
        return f"Overdue by {abs(days)}d"
    if days == 0:
        return "Due today"
    if days < 2:
        hours = days * 24
        return f"{hours}h"
    return f"{days}d"


def generate_insights(
    extracted: ExtractedFields,
    validation: ValidationResult,
    remedial: RemedialResult,
    confidence: ConfidenceScore,
) -> DocumentInsights:
    """Build a DocumentInsights object from the agent outputs."""

    # ── Field completeness ────────────────────────────────────────────────────
    filled = sum(
        1 for f in _EXPECTED_FIELDS
        if getattr(extracted, f, None) is not None
    )
    completeness = round(filled / len(_EXPECTED_FIELDS) * 100, 1)

    # ── Next service date ─────────────────────────────────────────────────────
    days_until_next = _days_until(extracted.next_service_date)
    is_overdue = days_until_next is not None and days_until_next < 0

    # ── Flags ────────────────────────────────────────────────────────────────
    flags: list[str] = []

    # Flags: focus on remedial findings and operational flags (completeness/overdue).
    if is_overdue:
        flags.append(f"Next service overdue by {abs(days_until_next)} days")
    elif days_until_next is not None and days_until_next <= 30:
        flags.append(f"Next service due in {days_until_next} days")
    if remedial.critical_items:
        flags.append(f"{len(remedial.critical_items)} critical finding(s)")
    if remedial.minor_items:
        flags.append(f"{len(remedial.minor_items)} minor finding(s)")
    if completeness < 70:
        flags.append(f"Only {completeness}% of expected fields found")
    # NOTE: validation.issues are intentionally NOT surfaced here — validation
    # checks are useful for routing but should not dominate the high-level
    # insights or the UI flags. This keeps the officer focused on document
    # content and key_readings from Content Understanding.

    # ── Score breakdown (for frontend charts) ────────────────────────────────
    score_breakdown = [
        {"label": "Extraction",  "score": round(confidence.extraction_score, 1),  "weight": 30},
        {"label": "Validation",  "score": round(confidence.validation_score, 1),   "weight": 30},
        {"label": "Remedial",    "score": round(confidence.remedial_score, 1),      "weight": 40},
    ]

    return DocumentInsights(
        compliance_status=_compliance_status(remedial, validation),
        risk_level=_risk_level(remedial, confidence.overall_score),
        days_until_next_service=days_until_next,
        is_overdue=is_overdue,
        fields_extracted=filled,
        fields_total=len(_EXPECTED_FIELDS),
        completeness_pct=completeness,
        flags=flags,
        sla_remaining=_sla_remaining(days_until_next),
        score_breakdown=score_breakdown,
    )
