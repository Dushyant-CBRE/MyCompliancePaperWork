"""
Agent 1: Extraction Agent (LLM-Based)
──────────────────────────────────────
Uses Azure OpenAI to extract structured fields from raw document text.
All field configurations are loaded from field_extraction_config.yaml.

Key features:
- Config-driven: field definitions, prompts, and examples come from YAML
- Dynamic schema generation: schema built from field config at runtime
- Confidence scoring: each field gets a 0-100 confidence score
- Fallback handling: uses configured fallback values for missing fields
"""
from __future__ import annotations

import json
import logging
import re

from backend.config import get_settings
from backend.models.document import ExtractedFields
from backend.utils.field_config import get_field_config_manager, generate_json_schema_from_config
from backend.utils.llm_client import get_llm_client

logger = logging.getLogger(__name__)


def _generate_system_prompt() -> str:
    """Generate system prompt dynamically from field configuration."""
    manager = get_field_config_manager()
    fields = manager.get_all_fields()

    prompt = """\
You are a compliance document field extraction specialist.
You will receive raw text extracted from a PPM (Planned Preventive Maintenance) compliance document
and must extract specific fields from it.

EXTRACTION RULES:
1. Set a field to null if the information cannot be found in the document.
2. Confidence 0 = not found/guessed; 100 = explicitly stated and unambiguous.
3. For each field, provide a confidence score (0-100) in the field_name_confidence field.
4. For source quotes: copy the shortest verbatim phrase from the document. Set to null if field is null.
5. For date fields, use ISO 8601 format (YYYY-MM-DD). If only month/year is visible, use YYYY-MM-01.

FIELDS TO EXTRACT:
"""

    for field in fields:
        required_text = "(REQUIRED)" if field.required else "(Optional)"
        prompt += f"\n• {field.name} {required_text}\n"
        prompt += f"  Type: {field.type}\n"
        prompt += f"  Description: {field.description}\n"
        if field.examples:
            # Convert examples to strings, handling any nested structures
            example_strs = [str(ex) if isinstance(ex, str) else json.dumps(ex) for ex in field.examples[:2]]
            prompt += f"  Examples: {', '.join(example_strs)}\n"

    prompt += """\n
RESPONSE FORMAT:
Return a SINGLE JSON object with fields from the above list, confidence scores, and overall_extraction_confidence.
Use this structure (adjust for your specific fields):
{
  "field_name": "<value or null>",
  "field_name_confidence": <0-100>,
  "another_field": "<value or null>",
  "another_field_confidence": <0-100>,
  ...
  "overall_extraction_confidence": <0-100>
}

Important: Return ONLY valid JSON. No markdown, no comments, no extra text.
"""
    return prompt


def _parse_json(raw: str) -> dict:
    """Parse JSON from LLM response, handling markdown fences."""
    raw = (raw or "").strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw.strip() or "{}")
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON from response: %s", raw[:200])
        return {}


def _build_extracted_fields(data: dict, text_length: int) -> ExtractedFields:
    """
    Convert extracted data dict to ExtractedFields model,
    applying field config defaults where needed.
    """
    manager = get_field_config_manager()

    # Start with what we got from LLM
    fields_data = {k: v for k, v in data.items() if k in ExtractedFields.model_fields}

    # Apply fallback values for missing required fields
    for field_config in manager.get_required_fields():
        if field_config.name not in fields_data or fields_data[field_config.name] is None:
            if field_config.fallback_value is not None:
                fields_data[field_config.name] = field_config.fallback_value
                logger.debug(
                    f"Applied fallback value for {field_config.name}: {field_config.fallback_value}"
                )

    # Ensure overall_extraction_confidence is set
    if "overall_extraction_confidence" not in fields_data:
        # Calculate as average of found fields' confidence scores
        confidence_scores = [
            v for k, v in data.items()
            if k.endswith("_confidence") and isinstance(v, (int, float))
        ]
        fields_data["overall_extraction_confidence"] = (
            sum(confidence_scores) / len(confidence_scores) if confidence_scores else 50.0
        )

    fields_data["raw_text_length"] = text_length

    return ExtractedFields(**fields_data)


def run_extraction_agent(document_text: str) -> ExtractedFields:
    """
    Run Agent 1 against the provided document text using config-driven extraction.

    Parameters:
        document_text: Raw text extracted from the PDF

    Returns:
        ExtractedFields model with extracted values and confidence scores
    """
    settings = get_settings()
    client = get_llm_client()

    system_prompt = _generate_system_prompt()

    user_content = (
        "Extract the required fields from the following compliance document text:\n\n"
        f"---BEGIN DOCUMENT---\n{document_text}\n---END DOCUMENT---"
    )

    logger.info("Agent 1 (Extraction): extracting fields from %d chars", len(document_text))

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",  # Model name (deployment ID used instead by client)
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=settings.llm_temperature,
            max_completion_tokens=2048,
        )

        raw_json = response.choices[0].message.content or "{}"
        data = _parse_json(raw_json)

        result = _build_extracted_fields(data, len(document_text))

        logger.info(
            "Agent 1 result: site=%r ppm=%r date=%r confidence=%.1f%%",
            result.site_name,
            result.ppm_reference,
            result.inspection_date,
            result.overall_extraction_confidence,
        )
        return result

    except Exception as exc:
        logger.exception("Agent 1: extraction failed – %s", exc)
        # Return empty result with raw text length
        return ExtractedFields(raw_text_length=len(document_text))

