"""
Document Processor – Orchestrator
───────────────────────────────────
Ties together the full AI pipeline for a single document:

  1. Upload PDF → Blob Storage  (storage_service)
  2. Extract text from PDF       (pdf_extractor – PyMuPDF + GPT-4o Vision)
  3. Agentic Orchestrator        (orchestrator)
       ├─ Agent 1: Field Extraction   (extraction_agent)   ← called via tool
       ├─ Agent 2: Validation         (validation_agent)   ← called via tool
       ├─ Agent 3: Remedial Detection (remedial_agent)     ← called via tool
       └─ Feedback loops / re-extraction as needed
  4. Confidence Scoring          (confidence_scorer)
  5. Persist full result          (storage_service)

Each step updates the document status so the dashboard can track progress in
near real-time.
"""
from __future__ import annotations

import logging
from datetime import datetime

from backend.agents.orchestrator import run_orchestrator
from backend.models.document import (
    DocumentMetadata,
    DocumentRecord,
    DocumentStatus,
)
from backend.services.confidence_scorer import calculate_confidence
from backend.services.insights_service import generate_insights
from backend.services.pdf_extractor import extract_text_from_pdf
from backend.services.storage_service import save_document, save_document_text, upload_pdf_to_blob

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

        # Persist text to blob so the Q&A endpoint can retrieve it later
        save_document_text(document_id, document_text)

        # ── Step 3: Agentic Orchestrator ─────────────────────────────────────
        # The orchestrator runs an agentic loop: it calls extraction, validation,
        # and remedial tools in an order it decides, looping back to re-extract
        # low-confidence fields before validating.
        logger.info("[%s] Step 3: Running Agentic Orchestrator", document_id)
        extracted_fields, validation_result, remedial_result, agent_state = run_orchestrator(
            document_text=document_text,
            metadata=metadata,
            document_id=document_id,
        )

        record.extracted_fields = extracted_fields
        record.validation_result = validation_result
        record.remedial_result = remedial_result
        record.agent_state = agent_state
        save_document(record)

        # ── Step 4: Confidence Scoring + Routing ─────────────────────────────
        logger.info("[%s] Step 4: Calculating confidence score", document_id)
        confidence_score = calculate_confidence(
            extracted_fields, validation_result, remedial_result
        )
        record.confidence_score = confidence_score

        # ── Step 5: Generate Insights ─────────────────────────────────────────
        logger.info("[%s] Step 5: Generating document insights", document_id)
        record.insights = generate_insights(
            extracted_fields, validation_result, remedial_result, confidence_score
        )

        # If orchestrator routing conflicts with scorer, log and defer to scorer
        # (scorer uses auditable numerical thresholds; orchestrator advice is advisory)
        if (
            agent_state.orchestrator_routing
            and agent_state.orchestrator_routing != confidence_score.decision.value.upper()
        ):
            logger.info(
                "[%s] Orchestrator suggested %s; scorer decided %s – using scorer",
                document_id,
                agent_state.orchestrator_routing,
                confidence_score.decision,
            )

        record.status = confidence_score.decision
        record.processed_at = datetime.utcnow()
        save_document(record)

        logger.info(
            "[%s] Processing complete: status=%s overall_confidence=%.1f%% "
            "orchestrator_steps=%d",
            document_id,
            record.status,
            confidence_score.overall_score,
            agent_state.iterations,
        )

    except Exception as exc:
        logger.exception("[%s] Pipeline failed: %s", document_id, exc)
        record.status = DocumentStatus.REQUIRES_ATTENTION
        record.processed_at = datetime.utcnow()
        save_document(record)
        raise

    return record
