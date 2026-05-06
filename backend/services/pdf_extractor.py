"""
PDF Extractor Service
---------------------
Strategy:
1. Use PyMuPDF (fitz) to extract embedded text from a PDF.
2. If the page text is too short (likely a scanned/image-only PDF),
   convert the page to a PNG image and send it to GPT-4o Vision to
   transcribe the content – effectively replacing Azure Document Intelligence.
3. Returns a single combined string of the full document text.
"""
from __future__ import annotations

import base64
import io
import logging
from pathlib import Path

import fitz  # PyMuPDF

from backend.config import get_settings
from backend.utils.llm_client import get_llm_client

logger = logging.getLogger(__name__)

# If a page yields fewer characters than this, treat it as a scanned page
MIN_TEXT_CHARS_PER_PAGE = 50


def _pdf_bytes_to_base64_images(pdf_bytes: bytes, dpi: int = 150) -> list[str]:
    """Convert every page of a PDF to a base64-encoded PNG string."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images: list[str] = []
    for page in doc:
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        png_bytes = pix.tobytes("png")
        images.append(base64.b64encode(png_bytes).decode("utf-8"))
    doc.close()
    return images


def _extract_text_with_vision(base64_images: list[str]) -> str:
    """
    Send PDF page images to GPT-4o Vision and request a full text transcription.
    This replaces Azure Document Intelligence for scanned documents.
    """
    settings = get_settings()
    client = get_llm_client()

    system_prompt = (
        "You are a document transcription assistant. "
        "Your job is to extract ALL text content from the provided document page images "
        "exactly as it appears. Preserve structure: headings, table rows, bullet points, "
        "dates, reference numbers, site names, and any findings or remedial notes. "
        "Output plain text only — no markdown formatting, no commentary."
    )

    # Build the user message content: one image block per page
    content: list[dict] = [
        {"type": "text", "text": "Please transcribe all text from the following document pages:"}
    ]
    for img_b64 in base64_images:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": img_b64,
            },
        })

    response = client.chat.completions.create(
        model=settings.azure_openai_deployment_primary,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        temperature=0.0,
    )
    return response.choices[0].message.content or ""


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Main entry point.  Returns a single string with all document text.

    Fallback chain:
      1. Content Understanding prebuilt-documentAnalysis  (best OCR + KV pairs + tables)
      2. PyMuPDF embedded text extraction                 (fast, works on digital PDFs)
      3. Claude Vision                                    (last resort for scanned pages)
    """
    # ── Level 1: Content Understanding prebuilt ──────────────────────────────
    try:
        from backend.services.content_understanding import extract_text_with_prebuilt
        cu_text = extract_text_with_prebuilt(pdf_bytes)
        if cu_text and len(cu_text) > MIN_TEXT_CHARS_PER_PAGE:
            logger.info(
                "PDF text extracted via Content Understanding prebuilt (%d chars)",
                len(cu_text),
            )
            return cu_text
    except Exception as exc:
        logger.warning("Content Understanding prebuilt step raised: %s", exc)

    # ── Level 2: PyMuPDF embedded text ────────────────────────────────────────
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages_text: list[str] = []
        has_sparse_pages = False

        for page in doc:
            text = page.get_text("text").strip()
            pages_text.append(text)
            if len(text) < MIN_TEXT_CHARS_PER_PAGE:
                has_sparse_pages = True

        doc.close()

        if not has_sparse_pages:
            full_text = "\n\n".join(pages_text)
            logger.info(
                "PDF text extracted via PyMuPDF (%d chars, %d pages)",
                len(full_text),
                len(pages_text),
            )
            return full_text

        # ── Level 3: Claude Vision for scanned pages ─────────────────────────
        logger.info("Sparse text detected — switching to Claude Vision extraction")
        images = _pdf_bytes_to_base64_images(pdf_bytes)
        vision_text = _extract_text_with_vision(images)
        logger.info(
            "Claude Vision extracted %d chars from %d page images",
            len(vision_text),
            len(images),
        )
        return vision_text

    except Exception as exc:
        logger.exception("PDF extraction failed: %s", exc)
        raise
