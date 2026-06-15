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
import re

from backend.config import get_settings
from backend.models.document import RemedialClassification, RemedialResult
from backend.utils.llm_client import get_llm_client

logger = logging.getLogger(__name__)


def _parse_json(raw: str) -> dict:
    """Extract JSON from a Claude response that may wrap it in markdown code fences."""
    raw = (raw or "").strip()
    # Strip ```json ... ``` or ``` ... ``` fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw.strip() or "{}")

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


def _call_llm(model_deployment: str, document_text: str, evidence_block: dict | None = None) -> dict:
    client = get_llm_client()
    user_content = (
        "Analyse the following PPM compliance document and classify it:\n\n"
        f"---BEGIN DOCUMENT---\n{document_text}\n---END DOCUMENT---"
    )
    if evidence_block:
        # Append structured evidence JSON to the user content to help the LLM
        user_content += "\n\nStructured evidence:\n" + json.dumps(evidence_block, default=str)

    response = client.chat.completions.create(
        model=model_deployment,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.0,
    )
    raw_json = response.choices[0].message.content or "{}"
    logger.debug("Remedial LLM raw response: %s", raw_json)
    return _parse_json(raw_json)


def run_remedial_detection_agent(document_text: str, extracted: object | None = None) -> RemedialResult:
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

    # Deterministic checks using structured extracted fields (if provided)
    # Priority: if key_readings indicate out-of-range or flagged values, mark REMEDIAL_CRITICAL.
    try:
        key_readings = []
        if extracted is not None and hasattr(extracted, "key_readings"):
            key_readings = getattr(extracted, "key_readings") or []

        # Example deterministic rules applied to key_readings:
        # - If any reading name contains 'CO' or 'carbon monoxide' and value > threshold -> CRITICAL
        # - If any reading status contains 'fail' or 'out of range' -> CRITICAL
        critical_indicators = []
        minor_indicators = []
        for r in key_readings:
            name = (r.get("name") or "").lower()
            val_str = str(r.get("value") or "").replace("ppm", "").strip()
            status = (r.get("status") or "").lower()
            # Status-based rules
            if "fail" in status or "out of range" in status or "critical" in status:
                critical_indicators.append(f"{r.get('name')}: status={r.get('status')}")
                continue
            # Do not treat generic 'warn'/'advisory' statuses on temperature readings
            # as remedial by default. Temperature measurements are often informational
            # and should only be escalated when explicitly marked as fail/out-of-range.
            if ("warn" in status or "advisory" in status) and not ("temp" in name or "temperature" in name):
                minor_indicators.append(f"{r.get('name')}: status={r.get('status')}")

            # Numeric threshold rules (best-effort parse)
            try:
                val = float(re.sub(r"[^0-9.\-]", "", val_str)) if val_str else None
            except Exception:
                val = None

            if val is not None:
                # Example thresholds (domain-specific values may be adjusted):
                # CO (ppm) > 50 -> CRITICAL; 10-50 -> MINOR
                if "co" in name or "carbon monoxide" in name:
                    if val > 50:
                        critical_indicators.append(f"{r.get('name')}: {val}")
                    elif val >= 10:
                        minor_indicators.append(f"{r.get('name')}: {val}")

        # If deterministic criticals found, return CRITICAL immediately
        if critical_indicators:
            logger.info("Remedial deterministic: critical indicators found: %s", critical_indicators)
            return RemedialResult(
                classification=RemedialClassification.REMEDIAL_CRITICAL,
                classification_confidence=98.0,
                findings=critical_indicators,
                critical_items=critical_indicators,
                minor_items=minor_indicators,
                reasoning="Deterministic rule matched critical key readings.",
            )

        # If no criticals but some minor indicators, return REMEDIAL_MINOR deterministically
        # If the document's extracted overall outcome indicates a clear 'Good' / 'Satisfactory' completion,
        # treat as PASS when there are no deterministic critical indicators. This lets clearly completed
        # works with only documentation/minor advisory notes be marked compliant.
        try:
            overall_outcome = None
            if extracted is not None and hasattr(extracted, "overall_outcome"):
                overall_outcome = getattr(extracted, "overall_outcome")
            if overall_outcome:
                o = str(overall_outcome).lower()
                if any(k in o for k in ("good", "satisfactory", "pass", "complete", "completed")):
                    logger.info("Remedial deterministic: overall_outcome=%s suggests PASS; returning PASS", overall_outcome)
                    return RemedialResult(
                        classification=RemedialClassification.PASS,
                        classification_confidence=92.0,
                        findings=[f"Overall outcome: {overall_outcome}"],
                        critical_items=[],
                        minor_items=[],
                        reasoning="Document completion survey rated Good/Satisfactory and no critical key readings; treated as PASS.",
                    )
        except Exception:
            logger.exception("Failed to evaluate overall_outcome for deterministic PASS")

        if minor_indicators:
            logger.info("Remedial deterministic: minor indicators found: %s", minor_indicators)
            return RemedialResult(
                classification=RemedialClassification.REMEDIAL_MINOR,
                classification_confidence=85.0,
                findings=minor_indicators,
                critical_items=[],
                minor_items=minor_indicators,
                reasoning="Deterministic rule matched minor key readings.",
            )
    except Exception as exc:
        logger.exception("Remedial deterministic check failed: %s", exc)

    try:
        # Build evidence block to send to LLM when deterministic checks don't decide
        evidence_block = None
        try:
            if extracted is not None:
                evidence_block = {
                    "extracted_fields_summary": {
                        "overall_extraction_confidence": getattr(extracted, "overall_extraction_confidence", None),
                        "site_name": getattr(extracted, "site_name", None),
                        "ppm_reference": getattr(extracted, "ppm_reference", None),
                        "inspection_date": getattr(extracted, "inspection_date", None),
                        "inspector_name": getattr(extracted, "inspector_name", None),
                        "document_type": getattr(extracted, "document_type", None),
                    },
                    "key_readings": getattr(extracted, "key_readings", []),
                }
        except Exception:
            evidence_block = None

        data = _call_llm(settings.azure_openai_deployment_primary, document_text, evidence_block=evidence_block)
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
