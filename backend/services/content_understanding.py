"""
Azure AI Content Understanding Service
────────────────────────────────────────
Provides two extraction strategies for compliance PDFs:

  1. Custom analyzer  — uses the 'compliance-cert-analyzer' trained on our schema.
                        Returns ExtractedFields directly. Skips Agent 1 entirely.
  2. Prebuilt analyzer — uses 'prebuilt-documentAnalysis'. Returns raw text +
                         auto-detected key-value pairs. Agent 1 still runs but
                         gets much richer input than plain PyMuPDF text.

Fallback chain (called by pdf_extractor.py):
  custom analyzer → prebuilt analyzer → PyMuPDF / Claude Vision

Both strategies use AzureKeyCredential — no Azure login required.
"""
from __future__ import annotations

import logging
import time
from typing import Optional

from azure.core.credentials import AzureKeyCredential

from backend.config import get_settings
from backend.models.document import ExtractedFields

logger = logging.getLogger(__name__)

# Polling config for long-running analysis operations
_POLL_INTERVAL_S = 2
_POLL_TIMEOUT_S = 120


def _get_client():
    """Build and return an Azure AI ContentUnderstandingClient."""
    try:
        from azure.ai.contentunderstanding import ContentUnderstandingClient  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "azure-ai-contentunderstanding not installed. "
            "Run: pip install azure-ai-contentunderstanding"
        ) from exc

    settings = get_settings()
    return ContentUnderstandingClient(
        endpoint=settings.azure_content_understanding_endpoint,
        credential=AzureKeyCredential(settings.azure_content_understanding_key),
        connection_verify=False,  # required for Azure AI Foundry corporate SSL chain
    )


def _poll_result(poller) -> dict:
    """Wait for a long-running operation and return the result as a dict."""
    deadline = time.monotonic() + _POLL_TIMEOUT_S
    while not poller.done():
        if time.monotonic() > deadline:
            raise TimeoutError("Content Understanding analysis timed out")
        time.sleep(_POLL_INTERVAL_S)
    return poller.result()


def _safe_str(field) -> Optional[str]:
    """Extract string value from a Content Understanding field object."""
    if field is None:
        return None
    # SDK v1.1 uses valueString; fallback to value or content
    val = (
        getattr(field, "value_string", None)
        or getattr(field, "valueString", None)
        or getattr(field, "value", None)
        or getattr(field, "content", None)
    )
    if val is None and hasattr(field, "as_dict"):
        d = field.as_dict()
        val = d.get("valueString") or d.get("value") or d.get("content")
    return str(val).strip() if val else None


def _safe_date(field) -> Optional[str]:
    """Extract date string (ISO format) from a Content Understanding field."""
    if field is None:
        return None
    val = (
        getattr(field, "value_date", None)
        or getattr(field, "valueDate", None)
        or getattr(field, "value", None)
        or getattr(field, "content", None)
    )
    if val is None and hasattr(field, "as_dict"):
        d = field.as_dict()
        val = d.get("valueDate") or d.get("value") or d.get("content")
    if val is None:
        return None
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val).strip() or None


def _safe_confidence(field) -> float:
    """Extract confidence score (0-100) from a Content Understanding field."""
    if field is None:
        return 0.0
    conf = getattr(field, "confidence", None)
    if conf is None and hasattr(field, "as_dict"):
        conf = field.as_dict().get("confidence")
    if conf is None and isinstance(field, dict):
        conf = field.get("confidence")
    if conf is None:
        return 50.0
    # SDK returns 0.0–1.0; convert to 0–100
    return round(float(conf) * 100, 1)


def _get_field(fields, key):
    """Get field from either an attribute dict or a plain dict."""
    if isinstance(fields, dict):
        return fields.get(key)
    return getattr(fields, key, None) if fields else None


def _zip_key_readings(result_fields: dict) -> list[dict]:
    """
    Reassemble parallel key_readings arrays into [{name, value, status}] list.
    The schema stores them as key_readings_names / _values / _statuses.
    """
    names_field = result_fields.get("key_readings_names")
    values_field = result_fields.get("key_readings_values")
    statuses_field = result_fields.get("key_readings_statuses")

    names = []
    values = []
    statuses = []

    if names_field:
        items = getattr(names_field, "value", []) or []
        names = [_safe_str(i) or "" for i in items]
    if values_field:
        items = getattr(values_field, "value", []) or []
        values = [_safe_str(i) or "" for i in items]
    if statuses_field:
        items = getattr(statuses_field, "value", []) or []
        statuses = [_safe_str(i) or "" for i in items]

    readings = []
    for i, name in enumerate(names):
        if not name:
            continue
        readings.append({
            "name": name,
            "value": values[i] if i < len(values) else "",
            "unit": None,
            "status": statuses[i] if i < len(statuses) else None,
        })
    return readings


def extract_with_custom_analyzer(pdf_bytes: bytes) -> Optional[ExtractedFields]:
    """
    Use the trained 'compliance-cert-analyzer' to extract fields directly.
    Returns ExtractedFields on success, None if not configured or on error.
    """
    settings = get_settings()
    analyzer = settings.azure_content_understanding_analyzer
    if not settings.azure_content_understanding_key or not analyzer:
        logger.info("Custom analyzer not configured — skipping")
        return None

    try:
        client = _get_client()
        logger.info("Content Understanding: submitting to custom analyzer '%s'", analyzer)

        poller = client.begin_analyze_binary(
            analyzer_id=analyzer,
            binary_input=pdf_bytes,
            content_type="application/pdf",
        )
        result = _poll_result(poller)

        # Navigate to fields — SDK v1.1 structure: result.contents[0].fields
        contents = getattr(result, "contents", None) or []
        if not contents:
            logger.warning("Custom analyzer returned no contents")
            return None

        fields = getattr(contents[0], "fields", {}) or {}
        if not fields and hasattr(contents[0], "as_dict"):
            fields = contents[0].as_dict().get("fields", {})

        extracted = ExtractedFields(
            site_name=_safe_str(fields.get("site_name")),
            site_name_confidence=_safe_confidence(fields.get("site_name")),
            ppm_reference=_safe_str(fields.get("ppm_reference")),
            ppm_reference_confidence=_safe_confidence(fields.get("ppm_reference")),
            inspection_date=_safe_date(fields.get("inspection_date")),
            inspection_date_confidence=_safe_confidence(fields.get("inspection_date")),
            next_service_date=_safe_date(fields.get("next_service_date")),
            next_service_date_confidence=_safe_confidence(fields.get("next_service_date")),
            inspector_name=_safe_str(fields.get("inspector_name")),
            inspector_name_confidence=_safe_confidence(fields.get("inspector_name")),
            vendor_name=_safe_str(fields.get("vendor_name")),
            vendor_name_confidence=_safe_confidence(fields.get("vendor_name")),
            client_name=_safe_str(fields.get("client_name")),
            client_name_confidence=_safe_confidence(fields.get("client_name")),
            document_type=_safe_str(fields.get("document_type")),
            document_type_confidence=_safe_confidence(fields.get("document_type")),
            certificate_number=_safe_str(fields.get("certificate_number")),
            certificate_number_confidence=_safe_confidence(fields.get("certificate_number")),
            overall_outcome=_safe_str(fields.get("overall_outcome")),
            overall_outcome_confidence=_safe_confidence(fields.get("overall_outcome")),
            equipment_id=_safe_str(fields.get("equipment_id")),
            equipment_id_confidence=_safe_confidence(fields.get("equipment_id")),
            key_readings=_zip_key_readings(fields),
            overall_extraction_confidence=_safe_confidence(
                getattr(contents[0], "confidence", None)
            ) or 70.0,
        )

        logger.info(
            "Custom analyzer extracted %d fields (overall confidence %.1f%%)",
            sum(1 for f in [extracted.site_name, extracted.inspector_name,
                            extracted.inspection_date, extracted.vendor_name,
                            extracted.ppm_reference] if f),
            extracted.overall_extraction_confidence,
        )
        return extracted

    except Exception as exc:
        logger.warning("Custom analyzer failed (%s) — will try prebuilt", exc)
        return None


def extract_text_with_prebuilt(pdf_bytes: bytes) -> Optional[str]:
    """
    Use 'prebuilt-documentAnalysis' to extract raw text + key-value pairs
    from the PDF. Returns a single enriched text string for Agent 1 to process.
    Returns None on error.
    """
    settings = get_settings()
    if not settings.azure_content_understanding_key:
        logger.info("Content Understanding key not set — skipping prebuilt")
        return None

    try:
        client = _get_client()
        logger.info("Content Understanding: submitting to prebuilt-documentAnalysis")

        poller = client.begin_analyze_document(
            analyzer_id="prebuilt-document",
            binary_input=pdf_bytes,
            content_type="application/pdf",
        )
        result = _poll_result(poller)

        # SDK v1.1: result.contents[0] has markdown + fields
        contents = getattr(result, "contents", None) or []
        if not contents:
            return None

        lines: list[str] = []

        # Rich markdown text (full OCR with structure preserved)
        markdown = getattr(contents[0], "markdown", None)
        if markdown:
            lines.append(markdown)

        # Key-value pairs from fields dict
        fields = getattr(contents[0], "fields", {}) or {}
        if fields:
            lines.append("\n--- Detected Key-Value Pairs ---")
            for k, v in fields.items():
                val = _safe_str(v) or _safe_date(v) or ""
                if val:
                    lines.append(f"{k}: {val}")

        full_text = "\n".join(lines)
        logger.info(
            "Prebuilt analyzer extracted %d chars, %d KV pairs, %d tables",
            len(full_text),
            len(kv_pairs),
            len(tables),
        )
        return full_text

    except Exception as exc:
        logger.warning("Prebuilt analyzer failed (%s) — will fall back to PyMuPDF", exc)
        return None
