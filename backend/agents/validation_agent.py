"""
Agent 2: Validation Agent
─────────────────────────
Uses GPT-4o to cross-check the extracted fields against expected metadata
supplied at upload time (expected site name, PPM reference, document type).

Produces a ValidationResult with per-field match scores and an overall
validation confidence score.
"""
from __future__ import annotations

import json
import logging

from datetime import date

from backend.config import get_settings
from backend.models.document import DocumentMetadata, ExtractedFields, ValidationResult
from backend.utils.llm_client import get_llm_client

logger = logging.getLogger(__name__)


def _build_system_prompt() -> str:
    today = date.today().isoformat()
    return f"""\
You are a compliance document validation specialist.
Today's date is {today}. Use this when evaluating whether inspection_date is in the past.

You will receive:
  1. "extracted" – fields pulled from the document by an AI extractor.
  2. "expected"  – metadata that the compliance officer provided at upload time.

Your task is to judge how well the extracted fields match the expected values
and assess whether the document dates and inspector details look legitimate.

Return a single JSON object with this exact schema – no other text:
{{
  "site_name_match":              <0-100>,
  "ppm_reference_match":          <0-100>,
  "date_valid":                   <true|false>,
  "date_validity_score":          <0-100>,
  "inspector_valid":              <true|false>,
  "inspector_validity_score":     <0-100>,
  "issues":                       ["<issue description>", ...],
  "overall_validation_confidence":<0-100>
}}

Scoring rules:
- site_name_match: 100 = exact (case-insensitive) match; 80 = abbreviation/alias match; 0 = completely different.
- ppm_reference_match: 100 = exact; partial/reformatted = 60; missing = 0.
- date_valid: true if inspection_date is on or before today ({today}) and not more than 5 years ago.
- date_validity_score: 100 if date_valid; 0 if future date; 50 if date missing.
- inspector_valid: true if inspector_name is present and looks like a real name (not "N/A", "Unknown", or empty).
- inspector_validity_score: 100 if valid; 0 if missing or placeholder.
- issues: list any discrepancies, mismatches, or concerns (empty list if none).
- overall_validation_confidence: weighted average:
    (site_name_match * 0.35) + (ppm_reference_match * 0.30) + (date_validity_score * 0.20) + (inspector_validity_score * 0.15)
- If an expected field was not provided (null), treat that field match as 70 (cannot confirm but not penalised).
"""


def run_validation_agent(
    extracted: ExtractedFields,
    metadata: DocumentMetadata | None,
) -> ValidationResult:
    """
    Run Agent 2 against extracted fields and expected metadata.
    Returns a ValidationResult with match scores and issues.
    """
    settings = get_settings()
    client = get_llm_client()

    # Build the payload the LLM will see
    extracted_payload = {
        "site_name": extracted.site_name,
        "ppm_reference": extracted.ppm_reference,
        "inspection_date": extracted.inspection_date,
        "inspector_name": extracted.inspector_name,
        "document_type": extracted.document_type,
    }

    expected_payload: dict = {}
    if metadata:
        expected_payload = {
            "site_name": metadata.expected_site_name,
            "ppm_reference": metadata.expected_ppm_reference,
            "document_type": metadata.expected_document_type,
        }

    user_content = (
        "Validate the extracted document fields against the expected values:\n\n"
        f"extracted: {json.dumps(extracted_payload, default=str)}\n"
        f"expected:  {json.dumps(expected_payload, default=str)}"
    )

    logger.info("Agent 2 (Validation): cross-checking extracted vs expected metadata")

    try:
        response = client.chat.completions.create(
            model=settings.azure_openai_deployment_primary,
            messages=[
                {"role": "system", "content": _build_system_prompt()},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )

        raw_json = response.choices[0].message.content or "{}"
        data = json.loads(raw_json)
        result = ValidationResult(
            **{k: v for k, v in data.items() if k in ValidationResult.model_fields}
        )
        logger.info(
            "Agent 2 result: site_match=%.0f%% ppm_match=%.0f%% date_valid=%s confidence=%.1f%%",
            result.site_name_match,
            result.ppm_reference_match,
            result.date_valid,
            result.overall_validation_confidence,
        )
        return result

    except json.JSONDecodeError as exc:
        logger.exception("Agent 2: JSON parse failed – %s", exc)
        return ValidationResult()
    except Exception as exc:
        logger.exception("Agent 2: unexpected error – %s", exc)
        raise
