"""
PDF Extractor Service - LLM-Based OCR
──────────────────────────────────────
Strategy:
1. Use PyMuPDF (fitz) to extract embedded text from a PDF.
2. If the page text is too short (likely a scanned/image-only PDF),
   convert the page to a PNG image and send it to Azure OpenAI Vision to
   transcribe the content – effectively replacing Document Intelligence.
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
    Send PDF page images to Azure OpenAI Vision and request a full text transcription.
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
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{img_b64}",
            },
        })

    response = client.chat.completions.create(
        model="gpt-4-vision",  # Model name (deployment ID used instead)
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        temperature=0.0,
    )
    return response.choices[0].message.content or ""


def extract_text_from_pdf(pdf_bytes: bytes) -> tuple[str, str]:
    """
    Main entry point. Returns (text, extraction_method).

    Fallback chain:
      1. PyMuPDF embedded text extraction  (fast, works on digital PDFs)
      2. Azure OpenAI Vision              (for scanned pages)
    """
    # ── Level 1: PyMuPDF embedded text ────────────────────────────────────────
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages_text: list[str] = []
        has_sparse_pages = False

        for page_idx, page in enumerate(doc):
            text = page.get_text("text").strip()
            pages_text.append(text)
            if len(text) < MIN_TEXT_CHARS_PER_PAGE:
                has_sparse_pages = True
                logger.debug(f"Page {page_idx + 1} has sparse text ({len(text)} chars)")

        doc.close()

        if not has_sparse_pages:
            full_text = "\n\n".join(pages_text)
            logger.info(
                "PDF text extracted via PyMuPDF (%d chars, %d pages)",
                len(full_text),
                len(pages_text),
            )
            return full_text, "PyMuPDF"

        # ── Level 2: Azure OpenAI Vision for scanned pages ──────────────────
        logger.info("Sparse text detected — switching to Azure OpenAI Vision extraction")
        images = _pdf_bytes_to_base64_images(pdf_bytes)
        vision_text = _extract_text_with_vision(images)
        logger.info(
            "Azure OpenAI Vision extracted %d chars from %d page images",
            len(vision_text),
            len(images),
        )
        return vision_text, "Azure OpenAI Vision"

    except Exception as exc:
        logger.exception("PDF extraction failed: %s", exc)
        raise

        raise
