"""
Critic Agent
─────────────
An LLM-based self-reflection / critic step that runs *after* the extraction,
validation, and remedial agents have completed their analysis.

Purpose
───────
The critic reviews the combined output and asks:
  1. Are the extracted fields consistent with what is actually in the document?
  2. Is the remedial classification (flag vs. no-flag) well-supported by evidence?
  3. Are there critical safety issues or compliance gaps that the remedial agent
     may have overlooked?

The result is a CriticFeedback dataclass that the orchestrator can use to:
  - Inject correction prompts back into the agent loop when the critic disagrees
  - Adjust the final confidence score up or down

Usage
─────
    from backend.agents.critic_agent import run_critic, CriticFeedback

    feedback = run_critic(
        document_text=...,
        extracted_fields=...,
        validation_result=...,
        remedial_result=...,
    )
    if not feedback.agreed:
        # re-run relevant agents with feedback injected
        ...
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

from backend.config import get_settings
from backend.utils.llm_client import get_llm_client

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Output model
# ---------------------------------------------------------------------------

@dataclass
class CriticFeedback:
    agreed: bool                                  # True = critic agrees with agents
    concerns: list[str] = field(default_factory=list)   # specific issues found
    revised_classification: str | None = None     # e.g. "REMEDIAL" if critic upgrades
    confidence_delta: float = 0.0                 # positive = more confident; negative = less
    raw_response: str = ""                        # full LLM text (for debugging)


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are a senior compliance document reviewer performing a critical review of an AI system's analysis.

Your task:
1. Read the document text and the AI's extracted fields, validation results, and remedial classification.
2. Decide whether the analysis is accurate and well-supported.
3. Identify any critical safety issues, misclassifications, or missing compliance concerns.

You MUST respond with a JSON object — no markdown fences, no extra text — with exactly these keys:
{
  "agreed": <true|false>,
  "concerns": [<string>, ...],
  "revised_classification": <"REMEDIAL"|"NON_REMEDIAL"|"INDETERMINATE"|null>,
  "confidence_delta": <float between -0.3 and 0.3>
}

Rules:
- "agreed" = true if the AI's analysis is substantially correct.
- "agreed" = false if there are material errors, missed safety issues, or the classification appears wrong.
- "concerns" should list each specific problem you found (max 5 items, concise).
- "revised_classification" is null unless you disagree with the remedial classification.
- "confidence_delta" reflects how much you think the confidence should change (+0.1 = more confident, -0.2 = less confident).

Be strict. Document compliance failures are serious. When in doubt, flag it."""


# ---------------------------------------------------------------------------
# Helper: strip markdown fences and parse JSON
# ---------------------------------------------------------------------------

def _parse_json(text: str) -> dict:
    """Strip markdown code fences then parse JSON. Raises ValueError on failure."""
    clean = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Critic returned invalid JSON: {exc}\n\nRaw: {text}") from exc


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_critic(
    document_text: str,
    extracted_fields: dict,
    validation_result: dict,
    remedial_result: dict,
) -> CriticFeedback:
    """
    Run the critic agent over a completed analysis pass.

    Parameters
    ----------
    document_text     : Raw text extracted from the document
    extracted_fields  : Dict of field→value from the extraction agent
    validation_result : Dict output of the validation agent
    remedial_result   : Dict output of the remedial detection agent

    Returns
    -------
    CriticFeedback with agreed, concerns, revised_classification, confidence_delta
    """
    settings = get_settings()
    client = get_llm_client()

    # Truncate document text to avoid exceeding context window (keep first ~4k chars)
    doc_preview = document_text[:4000] if len(document_text) > 4000 else document_text
    truncated = len(document_text) > 4000

    user_message = (
        f"## Document Text{'  [TRUNCATED — first 4000 chars shown]' if truncated else ''}\n"
        f"{doc_preview}\n\n"
        f"## Extracted Fields\n{json.dumps(extracted_fields, indent=2, default=str)}\n\n"
        f"## Validation Result\n{json.dumps(validation_result, indent=2, default=str)}\n\n"
        f"## Remedial Detection Result\n{json.dumps(remedial_result, indent=2, default=str)}\n\n"
        "Please provide your critical review as a JSON object."
    )

    raw = ""
    try:
        response = client.messages.create(
            model=settings.azure_openai_deployment_primary,
            max_tokens=512,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = (response.content[0].text or "").strip()
        parsed = _parse_json(raw)

        return CriticFeedback(
            agreed=bool(parsed.get("agreed", True)),
            concerns=list(parsed.get("concerns", [])),
            revised_classification=parsed.get("revised_classification"),
            confidence_delta=float(parsed.get("confidence_delta", 0.0)),
            raw_response=raw,
        )

    except Exception as exc:
        # Critic failure is non-fatal — log and return neutral feedback
        logger.warning("Critic agent failed (non-fatal): %s\nRaw: %s", exc, raw)
        return CriticFeedback(
            agreed=True,
            concerns=[],
            revised_classification=None,
            confidence_delta=0.0,
            raw_response=raw,
        )
