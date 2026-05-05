"""
Agent 1: Extraction Agent
─────────────────────────
Uses GPT-4o to extract structured fields from raw document text.

Fields extracted
----------------
- site_name          : The facility/building name
- ppm_reference      : Planned Preventive Maintenance reference number
- inspection_date    : Date the inspection was carried out
- inspector_name     : Name of the inspector / engineer
- equipment_id       : Asset/equipment identifier
- document_type      : Type of PPM (e.g. Fire Safety, HVAC, Electrical)
- vendor_name        : Vendor / contractor company name

Each field is returned with a 0-100 confidence score.
"""
from __future__ import annotations

import json
import logging

from backend.config import get_settings
from backend.models.document import ExtractedFields
from backend.utils.llm_client import get_llm_client

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a compliance document field extraction specialist.
You will receive raw text extracted from a PPM (Planned Preventive Maintenance) \
compliance document and must extract specific fields from it.

Return a single JSON object with this exact schema – no other text:
{
  "site_name":               "<string or null>",
  "site_name_confidence":    <0-100>,
  "site_name_source":        "<verbatim sentence/phrase from the document that contains this value, or null>",
  "ppm_reference":           "<string or null>",
  "ppm_reference_confidence":<0-100>,
  "ppm_reference_source":    "<verbatim sentence/phrase or null>",
  "inspection_date":         "<ISO 8601 date string or null>",
  "inspection_date_confidence":<0-100>,
  "inspection_date_source":  "<verbatim sentence/phrase or null>",
  "inspector_name":          "<string or null>",
  "inspector_name_confidence":<0-100>,
  "inspector_name_source":   "<verbatim sentence/phrase or null>",
  "equipment_id":            "<string or null>",
  "equipment_id_confidence": <0-100>,
  "equipment_id_source":     "<verbatim sentence/phrase or null>",
  "document_type":           "<string or null>",
  "document_type_confidence":<0-100>,
  "document_type_source":    "<verbatim sentence/phrase or null>",
  "vendor_name":             "<string or null>",
  "vendor_name_confidence":  <0-100>,
  "vendor_name_source":      "<verbatim sentence/phrase or null>",
  "certificate_number":      "<string or null>",
  "certificate_number_confidence": <0-100>,
  "certificate_number_source": "<verbatim sentence/phrase or null>",
  "next_service_date":       "<ISO 8601 date string or null>",
  "next_service_date_confidence": <0-100>,
  "next_service_date_source": "<verbatim sentence/phrase or null>",
  "overall_outcome":         "<string or null>",
  "overall_outcome_confidence": <0-100>,
  "overall_outcome_source":  "<verbatim sentence/phrase or null>",
  "client_name":             "<string or null>",
  "client_name_confidence":  <0-100>,
  "client_name_source":      "<verbatim sentence/phrase or null>",
  "key_readings":            [{"name":"<param name>","value":"<value>","unit":"<unit or null>","status":"<Pass/Fail/Advisory or null>"}],
  "overall_extraction_confidence": <0-100>
}

Rules:
- Set a field to null if the information cannot be found in the document.
- Confidence 0 = not found / guessed; 100 = explicitly stated and unambiguous.
- For source quotes: copy the shortest verbatim phrase or sentence from the document that contains the value. Keep it under 150 characters. Set to null if field is null.
- For inspection_date / next_service_date, use ISO 8601 format (YYYY-MM-DD). If only month/year is visible use YYYY-MM-01.
- For site_name look for: "Site:", "Location:", "Property:", "Premises:" labels or letterhead addresses.
- For ppm_reference look for: "Ref:", "Reference:", "Job No:", "PPM Ref:", "Work Order:" labels.
- For certificate_number look for: "Certificate No:", "Cert No:", "Certificate Number:", "Certificate Ref:" labels.
- For next_service_date look for: "Next Service:", "Next Inspection:", "Next Visit:", "Due Date:", "Review Date:" labels.
- For overall_outcome look for: "Outcome:", "Result:", "Status:", "Conclusion:", "All satisfactory", "Pass", "Fail" statements.
- For client_name look for: "Client:", "Customer:", "On behalf of:", "Prepared for:", "Building Owner:" labels.
- For key_readings extract any tabular measurement data (e.g. pH, conductivity, inhibitor levels, temperature, pressure). Each reading should have name, value, unit, and pass/fail status if stated.
- For document_type identify the maintenance category (Fire Safety, HVAC, Electrical Testing, \
  Legionella, Lift, Gas Safety, Water Treatment, etc.).
- overall_extraction_confidence is the weighted average of individual confidences for fields \
  that were found (ignore null fields).
"""


def run_extraction_agent(document_text: str) -> ExtractedFields:
    """
    Run Agent 1 against the provided document text.
    Returns an ExtractedFields model populated with values and confidence scores.
    """
    settings = get_settings()
    client = get_llm_client()

    user_content = (
        "Extract the required fields from the following compliance document text:\n\n"
        f"---BEGIN DOCUMENT---\n{document_text}\n---END DOCUMENT---"
    )

    logger.info("Agent 1 (Extraction): sending %d chars to LLM", len(document_text))

    try:
        response = client.chat.completions.create(
            model=settings.azure_openai_deployment_primary,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )

        raw_json = response.choices[0].message.content or "{}"
        data = json.loads(raw_json)
        result = ExtractedFields(
            **{k: v for k, v in data.items() if k in ExtractedFields.model_fields},
            raw_text_length=len(document_text),
        )
        logger.info(
            "Agent 1 result: site=%r ppm=%r date=%r confidence=%.1f%%",
            result.site_name,
            result.ppm_reference,
            result.inspection_date,
            result.overall_extraction_confidence,
        )
        return result

    except json.JSONDecodeError as exc:
        logger.exception("Agent 1: JSON parse failed – %s", exc)
        return ExtractedFields(raw_text_length=len(document_text))
    except Exception as exc:
        logger.exception("Agent 1: unexpected error – %s", exc)
        raise
