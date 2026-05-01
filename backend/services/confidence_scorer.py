"""
Confidence Scorer
─────────────────
Combines the three agent outputs into a single weighted confidence score
and maps it to a routing decision (auto-approve / manual review / attention).

Weights (as defined in README):
  - Extraction  : 30 %
  - Validation  : 30 %
  - Remedial    : 40 %

Thresholds:
  - >= 85 %  → AUTO_APPROVED
  - 60–85 %  → MANUAL_REVIEW
  -  < 60 %  → REQUIRES_ATTENTION

Special override rule:
  - Any REMEDIAL_CRITICAL classification forces at minimum MANUAL_REVIEW,
    regardless of overall score.
"""
from __future__ import annotations

import logging

from backend.config import get_settings
from backend.models.document import (
    ConfidenceScore,
    DocumentStatus,
    ExtractedFields,
    RemedialClassification,
    RemedialResult,
    ValidationResult,
)

logger = logging.getLogger(__name__)


def calculate_confidence(
    extracted: ExtractedFields,
    validation: ValidationResult,
    remedial: RemedialResult,
) -> ConfidenceScore:
    """
    Compute a weighted overall confidence score and return a routing decision.
    """
    settings = get_settings()

    extraction_score = extracted.overall_extraction_confidence
    validation_score = validation.overall_validation_confidence
    remedial_score = remedial.classification_confidence

    overall = (
        extraction_score * settings.weight_extraction
        + validation_score * settings.weight_validation
        + remedial_score * settings.weight_remedial
    )

    # Determine base decision from thresholds
    if overall >= settings.confidence_auto_approve_threshold:
        decision = DocumentStatus.AUTO_APPROVED
    elif overall >= settings.confidence_manual_review_threshold:
        decision = DocumentStatus.MANUAL_REVIEW
    else:
        decision = DocumentStatus.REQUIRES_ATTENTION

    # Safety override: critical findings must never be auto-approved
    if remedial.classification == RemedialClassification.REMEDIAL_CRITICAL:
        if decision == DocumentStatus.AUTO_APPROVED:
            logger.warning(
                "Overriding AUTO_APPROVED → MANUAL_REVIEW due to REMEDIAL_CRITICAL classification"
            )
            decision = DocumentStatus.MANUAL_REVIEW

    score = ConfidenceScore(
        extraction_score=round(extraction_score, 2),
        validation_score=round(validation_score, 2),
        remedial_score=round(remedial_score, 2),
        overall_score=round(overall, 2),
        decision=decision,
    )

    logger.info(
        "Confidence: extract=%.1f%% validation=%.1f%% remedial=%.1f%% → overall=%.1f%% [%s]",
        extraction_score,
        validation_score,
        remedial_score,
        overall,
        decision,
    )

    return score
