"""
Upload Router  –  POST /api/upload
───────────────────────────────────
Accepts a PDF file multipart upload plus optional metadata fields.
Triggers the full AI processing pipeline synchronously and returns
the initial document record.

For a production system with large volumes, this would enqueue a
message and return immediately (async processing). For the hackathon
demo, synchronous processing is fine and simpler to demonstrate.
"""
from __future__ import annotations

from datetime import datetime
import logging

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from backend.models.document import DocumentMetadata, UploadResponse
from backend.services.document_processor import process_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["upload"])

# Max upload size: 20 MB
_MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024


@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF compliance document"),
    expected_site_name: str | None = Form(None),
    expected_ppm_type: str | None = Form(None),
    expected_document_date: datetime | None = Form(None),
    expected_document_type: str | None = Form(None),
    expected_vendor_name: str | None = Form(None),
    notes: str | None = Form(None),
):
    """
    Upload a PPM compliance PDF for AI processing.

    The document is processed immediately (extraction → validation →
    remedial detection → confidence scoring) and the result is stored.
    Returns the document_id immediately; poll GET /api/documents/{id}
    for the full result.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    pdf_bytes = await file.read()

    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(pdf_bytes) > _MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {_MAX_FILE_SIZE_BYTES // 1024 // 1024} MB.",
        )

    metadata = DocumentMetadata(
        expected_site_name=expected_site_name,
        expected_ppm_type=expected_ppm_type,
        expected_document_date=expected_document_date,
        expected_document_type=expected_document_type,
        expected_vendor_name=expected_vendor_name,
        notes=notes,
    )

    # Run processing in a background task so the HTTP response returns quickly
    # The status starts as 'processing'; the client polls for completion.
    def _run():
        try:
            process_document(pdf_bytes, file.filename or "document.pdf", metadata)
        except Exception as exc:
            logger.exception("Background processing failed: %s", exc)

    # For demo we kick off in the background and return 202 Accepted
    # To get the document_id we need to kick off synchronously for a moment
    # then hand off – simplest for hackathon: process fully synchronously
    try:
        record = process_document(pdf_bytes, file.filename or "document.pdf", metadata)
    except Exception as exc:
        logger.exception("Document processing error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(exc)}")

    return UploadResponse(
        document_id=record.document_id,
        filename=record.filename,
        message=(
            f"Document processed successfully. "
            f"Status: {record.status}. "
            f"Confidence: {record.confidence_score.overall_score if record.confidence_score else 0:.1f}%"
        ),
    )
