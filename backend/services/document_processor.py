"""
Document Processor – Orchestrator
───────────────────────────────────
Ties together the full AI pipeline for a single document:

  1. Upload PDF → Blob Storage  (storage_service)
  2. Extract text from PDF       (pdf_extractor – PyMuPDF + GPT-4o Vision)
  3. Agent 1: Field Extraction   (extraction_agent)
  4. Agent 2: Validation         (validation_agent)
  5. Agent 3: Remedial Detection (remedial_agent)
  6. Confidence Scoring          (confidence_scorer)
  7. Persist full result          (storage_service)

Each step updates the document status so the dashboard can track progress in
near real-time.
"""
from __future__ import annotations

import logging
from datetime import datetime

from backend.agents.extraction_agent import run_extraction_agent
from backend.agents.remedial_agent import run_remedial_detection_agent
from backend.agents.validation_agent import run_validation_agent
from backend.models.document import (
    DocumentMetadata,
    DocumentRecord,
    DocumentStatus,
)
from backend.services.confidence_scorer import calculate_confidence
from backend.services.pdf_extractor import extract_text_from_pdf
from backend.services.storage_service import save_document, upload_pdf_to_blob

logger = logging.getLogger(__name__)


def process_document(
    pdf_bytes: bytes,
    filename: str,
    metadata: DocumentMetadata | None = None,
) -> DocumentRecord:
    """
    Full end-to-end document processing pipeline.

    Parameters
    ----------
    pdf_bytes : Raw PDF file bytes.
    filename  : Original filename (used for blob naming and display).
    metadata  : Optional officer-supplied metadata for validation cross-check.

    Returns
    -------
    The completed DocumentRecord with all agent results populated.
    """
    # ── Step 1: Upload to Blob Storage ───────────────────────────────────────
    logger.info("Processing document: %s", filename)
    document_id, blob_url = upload_pdf_to_blob(pdf_bytes, filename)

    record = DocumentRecord(
        document_id=document_id,
        filename=filename,
        blob_url=blob_url,
        status=DocumentStatus.PROCESSING,
        metadata=metadata,
    )
    save_document(record)

    try:
        # ── Step 2: PDF Text Extraction ──────────────────────────────────────
        logger.info("[%s] Step 2: Extracting text from PDF", document_id)
        document_text = extract_text_from_pdf(pdf_bytes)

        # ── Step 3: Agent 1 – Field Extraction ───────────────────────────────
        logger.info("[%s] Step 3: Running Extraction Agent", document_id)
        extracted_fields = run_extraction_agent(document_text)
        record.extracted_fields = extracted_fields
        save_document(record)

        # ── Step 4: Agent 2 – Validation ─────────────────────────────────────
        logger.info("[%s] Step 4: Running Validation Agent", document_id)
        validation_result = run_validation_agent(extracted_fields, metadata)
        record.validation_result = validation_result
        save_document(record)

        # ── Step 5: Agent 3 – Remedial Detection ─────────────────────────────
        logger.info("[%s] Step 5: Running Remedial Detection Agent", document_id)
        remedial_result = run_remedial_detection_agent(document_text)
        record.remedial_result = remedial_result
        save_document(record)

        # ── Step 6: Confidence Scoring + Routing ─────────────────────────────
        logger.info("[%s] Step 6: Calculating confidence score", document_id)
        confidence_score = calculate_confidence(
            extracted_fields, validation_result, remedial_result
        )
        record.confidence_score = confidence_score
        record.status = confidence_score.decision
        record.processed_at = datetime.utcnow()
        save_document(record)

        logger.info(
            "[%s] Processing complete: status=%s overall_confidence=%.1f%%",
            document_id,
            record.status,
            confidence_score.overall_score,
        )

    except Exception as exc:
        logger.exception("[%s] Pipeline failed: %s", document_id, exc)
        record.status = DocumentStatus.REQUIRES_ATTENTION
        record.processed_at = datetime.utcnow()
        save_document(record)
        raise

    return record
