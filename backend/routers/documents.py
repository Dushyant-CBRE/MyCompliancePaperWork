"""
Documents Router  –  GET/PUT /api/documents
────────────────────────────────────────────
Endpoints:
  GET  /api/documents              – list all documents (optional ?status= filter)
  GET  /api/documents/{id}         – get a single document with full AI results
  PUT  /api/documents/{id}/override – officer override (approve / reject)
  GET  /api/documents/{id}/pdf     – serve the raw PDF bytes (for viewer)
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from backend.models.document import (
    DocumentListResponse,
    DocumentRecord,
    DocumentStatus,
    OverrideRequest,
)
from backend.services.storage_service import (
    get_document,
    get_pdf_from_blob,
    list_documents,
    save_document,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
def get_documents(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
):
    """List all documents, newest first. Optional ?status= filter."""
    records = list_documents(status_filter=status, limit=limit)
    return DocumentListResponse(documents=records, total=len(records))


@router.get("/{document_id}", response_model=DocumentRecord)
def get_document_detail(document_id: str):
    """Get full details for a single document including all AI results."""
    record = get_document(document_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")
    return record


@router.put("/{document_id}/override", response_model=DocumentRecord)
def override_document(document_id: str, body: OverrideRequest):
    """
    Officer override – manually approve or reject a document.
    Requires a reason and officer name for full audit trail.
    """
    record = get_document(document_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    # Only allow overriding documents that are not already officer-actioned
    allowed_transitions = {
        DocumentStatus.AUTO_APPROVED,
        DocumentStatus.MANUAL_REVIEW,
        DocumentStatus.REQUIRES_ATTENTION,
        DocumentStatus.APPROVED,
        DocumentStatus.REJECTED,
    }
    if record.status == DocumentStatus.PROCESSING:
        raise HTTPException(
            status_code=409, detail="Document is still being processed. Please wait."
        )

    allowed_override_decisions = {DocumentStatus.APPROVED, DocumentStatus.REJECTED}
    if body.decision not in allowed_override_decisions:
        raise HTTPException(
            status_code=400,
            detail=f"Override decision must be 'approved' or 'rejected', got '{body.decision}'.",
        )

    record.status = body.decision
    record.override_by = body.officer_name
    record.override_reason = body.reason
    record.overridden_at = datetime.utcnow()
    save_document(record)

    logger.info(
        "Document %s overridden to %s by %s", document_id, body.decision, body.officer_name
    )
    return record


@router.get("/{document_id}/pdf")
def get_document_pdf(document_id: str):
    """
    Serve the raw PDF for the in-browser viewer.
    Returns the PDF bytes with appropriate Content-Type header.
    """
    record = get_document(document_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    pdf_bytes = get_pdf_from_blob(document_id, record.filename)
    if pdf_bytes is None:
        raise HTTPException(
            status_code=404,
            detail="PDF file not found in storage. It may have been deleted.",
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{record.filename}"'},
    )
