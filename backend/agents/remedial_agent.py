"""
Agent 3: Remedial Detection Agent
───────────────────────────────────
Uses GPT-4o (with GPT-4-turbo fallback) to analyse the full document text and
classify it as:
  - PASS             – No issues found, document is compliant.
  - REMEDIAL_MINOR   – Advisory/minor issues that need follow-up but not urgent.
  - REMEDIAL_CRITICAL – Failed compliance / safety-critical deficiencies requiring
                        immediate action.

This is the most important classification in the pipeline (40% of overall confidence
weighting) because false negatives on critical safety issues are unacceptable.
A second LLM call is made at a higher reasoning model (gpt-4-turbo) if the primary
model returns low confidence, to provide a safety net.
"""
from __future__ import annotations

import json
import logging

from backend.config import get_settings
from backend.models.document import RemedialClassification, RemedialResult
from backend.utils.llm_client import get_llm_client

logger = logging.getLogger(__name__)

# If the primary classification confidence is below this, escalate to the fallback model
_ESCALATION_THRESHOLD = 75.0

_SYSTEM_PROMPT = """\
You are a statutory compliance expert specialising in PPM (Planned Preventive Maintenance) \
documents for facilities management.

Analyse the provided document text and determine whether the inspection outcome is a PASS, \
indicates MINOR advisory issues, or has CRITICAL safety-compliance failures.

CRITICAL indicators (any one of these = REMEDIAL_CRITICAL):
- Explicit "FAIL" or "Failed" outcome statements
- Equipment or systems left inoperative / unsafe
- "Immediate action required" / "Do not use" language
- Legal non-compliance notices (e.g. L8, BS 7671, BS 5839, GS(IR)R violations)
- Fire suppression / alarm systems not functional
- Gas-related safety warnings
- Structural safety concerns

MINOR indicators (remedial advisory, not urgent):
- "Recommended" or "Advisory" actions noted
- Minor wear items that need scheduling
- Documentation gaps that require correction
- Items rated "Satisfactory but monitor"

PASS indicators:
- "All items satisfactory", "No deficiencies", "Compliant"
- All tested items passed with no follow-up required

Return a single JSON object with this exact schema – no other text:
{
  "classification":            "PASS" | "REMEDIAL_MINOR" | "REMEDIAL_CRITICAL",
  "classification_confidence": <0-100>,
  "findings":                  ["<finding text>", ...],
  "critical_items":            ["<critical item>", ...],
  "minor_items":               ["<minor item>", ...],
  "reasoning":                 "<1-3 sentence explanation of your classification decision>"
}

Rules:
- When in doubt between PASS and REMEDIAL_MINOR, choose REMEDIAL_MINOR (safer).
- When in doubt between REMEDIAL_MINOR and REMEDIAL_CRITICAL, choose REMEDIAL_CRITICAL (safer).
- classification_confidence: 90+ = very clear evidence; 70-90 = reasonable evidence; \
  <70 = ambiguous, likely needs human review.
- findings: list every significant finding mentioned (good or bad).
- critical_items / minor_items should quote directly from the document where possible.
"""


def _call_llm(model_deployment: str, document_text: str) -> dict:
    client = get_llm_client()
    user_content = (
        "Analyse the following PPM compliance document and classify it:\n\n"
        f"---BEGIN DOCUMENT---\n{document_text}\n---END DOCUMENT---"
    )
    response = client.chat.completions.create(
        model=model_deployment,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    raw_json = response.choices[0].message.content or "{}"
    return json.loads(raw_json)


def run_remedial_detection_agent(document_text: str) -> RemedialResult:
    """
    Run Agent 3 against the full document text.
    Escalates to the fallback model if primary confidence is below threshold.
    Returns a RemedialResult with classification and supporting evidence.
    """
    settings = get_settings()

    logger.info(
        "Agent 3 (Remedial): analysing %d chars with primary model (%s)",
        len(document_text),
        settings.azure_openai_deployment_primary,
    )

    try:
        data = _call_llm(settings.azure_openai_deployment_primary, document_text)
        confidence = float(data.get("classification_confidence", 0))

        # Escalate to fallback model if confidence is too low
        if confidence < _ESCALATION_THRESHOLD and settings.azure_openai_deployment_fallback:
            logger.warning(
                "Agent 3: primary confidence %.1f%% < threshold %.1f%% – escalating to %s",
                confidence,
                _ESCALATION_THRESHOLD,
                settings.azure_openai_deployment_fallback,
            )
            data = _call_llm(settings.azure_openai_deployment_fallback, document_text)
            confidence = float(data.get("classification_confidence", 0))

        classification_str = data.get("classification", "UNKNOWN")
        try:
            classification = RemedialClassification(classification_str)
        except ValueError:
            classification = RemedialClassification.UNKNOWN

        result = RemedialResult(
            classification=classification,
            classification_confidence=confidence,
            findings=data.get("findings", []),
            critical_items=data.get("critical_items", []),
            minor_items=data.get("minor_items", []),
            reasoning=data.get("reasoning", ""),
        )

        # ── Build structured evidence list for the Review UI ──────────────
        evidence: list[dict] = []
        for item in result.critical_items:
            evidence.append({"text": item, "page": 0, "severity": "High"})
        for item in result.minor_items:
            evidence.append({"text": item, "page": 0, "severity": "Medium"})
        # Add findings not already covered as advisory Low severity
        critical_set = set(result.critical_items)
        minor_set = set(result.minor_items)
        for f in result.findings:
            if f not in critical_set and f not in minor_set:
                evidence.append({"text": f, "page": 0, "severity": "Low"})
        result.evidence = evidence

        logger.info(
            "Agent 3 result: classification=%s confidence=%.1f%% critical_items=%d",
            result.classification,
            result.classification_confidence,
            len(result.critical_items),
        )
        return result

    except json.JSONDecodeError as exc:
        logger.exception("Agent 3: JSON parse failed – %s", exc)
        return RemedialResult()
    except Exception as exc:
        logger.exception("Agent 3: unexpected error – %s", exc)
        raise
