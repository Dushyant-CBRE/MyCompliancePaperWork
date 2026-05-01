"""
Tool schemas and bound implementations for the Orchestrator Agent.

Each tool is a Python function that the orchestrator dispatches when the LLM
emits a tool_call.  The functions close over an OrchestratorContext that holds
the document text, expected metadata, and the running agent results so that
individual tool calls don't need to re-pass large blobs of text.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

from backend.agents.extraction_agent import run_extraction_agent
from backend.agents.remedial_agent import run_remedial_detection_agent
from backend.agents.validation_agent import run_validation_agent
from backend.config import get_settings
from backend.models.document import (
    DocumentMetadata,
    ExtractedFields,
    RemedialResult,
    ValidationResult,
)
from backend.utils.llm_client import get_llm_client

logger = logging.getLogger(__name__)

# ── OpenAI function-calling schemas ──────────────────────────────────────────

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "extract_all_fields",
            "description": (
                "Run the extraction agent on the full document text. "
                "Extracts all structured compliance fields with confidence scores. "
                "Always call this first."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "re_extract_field",
            "description": (
                "Re-extract a single field whose confidence score is low (<60) or "
                "whose validation match score is poor (<50). Runs a targeted LLM call "
                "with a specific hint rather than the full extraction pass."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "field_name": {
                        "type": "string",
                        "description": "The field to re-extract.",
                        "enum": [
                            "site_name",
                            "ppm_reference",
                            "inspection_date",
                            "inspector_name",
                            "equipment_id",
                            "document_type",
                            "vendor_name",
                        ],
                    },
                    "context_hint": {
                        "type": "string",
                        "description": (
                            "Specific guidance for finding this field "
                            "(e.g. 'look in page header or footer', "
                            "'may be labelled as Job No or Work Order')."
                        ),
                    },
                },
                "required": ["field_name", "context_hint"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate_document",
            "description": (
                "Run the validation agent: cross-check the currently extracted fields "
                "against the expected metadata supplied at upload time. "
                "Call this after extract_all_fields (and any re_extract_field calls)."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detect_remedial_issues",
            "description": (
                "Run the remedial-detection agent: classify the document as "
                "PASS, REMEDIAL_MINOR, or REMEDIAL_CRITICAL. "
                "Call this after validation."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finalize",
            "description": (
                "Signal that processing is complete and record the orchestrator's "
                "routing recommendation. MUST be called once all required tools have run."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "routing_decision": {
                        "type": "string",
                        "enum": ["AUTO_APPROVED", "MANUAL_REVIEW", "REQUIRES_ATTENTION"],
                        "description": "Recommended routing decision.",
                    },
                    "rationale": {
                        "type": "string",
                        "description": "One-to-three sentence explanation of the decision.",
                    },
                },
                "required": ["routing_decision", "rationale"],
            },
        },
    },
]


# ── Shared context passed into every bound tool ───────────────────────────────

@dataclass
class OrchestratorContext:
    """Mutable state shared across all tool calls within one orchestration run."""

    document_text: str
    metadata: Optional[DocumentMetadata]

    # Latest agent outputs (updated in place by tools)
    extracted_fields: Optional[ExtractedFields] = None
    validation_result: Optional[ValidationResult] = None
    remedial_result: Optional[RemedialResult] = None

    # Orchestrator decision (set by finalize tool)
    routing_decision: Optional[str] = None
    rationale: str = ""
    finalized: bool = False

    # Step log for audit trail
    steps_log: list[dict] = field(default_factory=list)


# ── Tool implementations ──────────────────────────────────────────────────────

def tool_extract_all_fields(ctx: OrchestratorContext, args: dict) -> str:
    """Run the full extraction agent and update ctx.extracted_fields."""
    logger.info("Tool: extract_all_fields")
    ctx.extracted_fields = run_extraction_agent(ctx.document_text)
    ef = ctx.extracted_fields
    summary = {
        "site_name": ef.site_name,
        "site_name_confidence": ef.site_name_confidence,
        "ppm_reference": ef.ppm_reference,
        "ppm_reference_confidence": ef.ppm_reference_confidence,
        "inspection_date": ef.inspection_date,
        "inspection_date_confidence": ef.inspection_date_confidence,
        "inspector_name": ef.inspector_name,
        "inspector_name_confidence": ef.inspector_name_confidence,
        "document_type": ef.document_type,
        "document_type_confidence": ef.document_type_confidence,
        "vendor_name": ef.vendor_name,
        "vendor_name_confidence": ef.vendor_name_confidence,
        "overall_extraction_confidence": ef.overall_extraction_confidence,
    }
    ctx.steps_log.append({"tool": "extract_all_fields", "result": summary})
    return json.dumps(summary)


def tool_re_extract_field(ctx: OrchestratorContext, args: dict) -> str:
    """Targeted re-extraction of a single low-confidence field."""
    field_name: str = args["field_name"]
    context_hint: str = args["context_hint"]
    logger.info("Tool: re_extract_field(field=%s)", field_name)

    settings = get_settings()
    client = get_llm_client()

    prompt = (
        f"You are extracting a single field from a PPM compliance document.\n\n"
        f"Field to extract: {field_name}\n"
        f"Hint: {context_hint}\n\n"
        f"Document text:\n---BEGIN---\n{ctx.document_text}\n---END---\n\n"
        "Return ONLY a JSON object with this schema:\n"
        '{"value": "<extracted value or null>", "confidence": <0-100>}'
    )

    try:
        response = client.chat.completions.create(
            model=settings.azure_openai_deployment_primary,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        new_value = data.get("value")
        new_confidence = float(data.get("confidence", 0))

        # Patch the field on the current ExtractedFields object
        if ctx.extracted_fields is None:
            ctx.extracted_fields = ExtractedFields(raw_text_length=len(ctx.document_text))

        setattr(ctx.extracted_fields, field_name, new_value)
        setattr(ctx.extracted_fields, f"{field_name}_confidence", new_confidence)

        result = {"field": field_name, "new_value": new_value, "new_confidence": new_confidence}
    except Exception as exc:
        logger.exception("re_extract_field failed: %s", exc)
        result = {"field": field_name, "error": str(exc)}

    ctx.steps_log.append({"tool": "re_extract_field", "args": args, "result": result})
    return json.dumps(result)


def tool_validate_document(ctx: OrchestratorContext, args: dict) -> str:
    """Run validation agent with current extracted fields."""
    logger.info("Tool: validate_document")
    if ctx.extracted_fields is None:
        return json.dumps({"error": "extract_all_fields must be called before validate_document"})

    ctx.validation_result = run_validation_agent(ctx.extracted_fields, ctx.metadata)
    vr = ctx.validation_result
    summary = {
        "site_name_match": vr.site_name_match,
        "ppm_reference_match": vr.ppm_reference_match,
        "date_valid": vr.date_valid,
        "date_validity_score": vr.date_validity_score,
        "inspector_valid": vr.inspector_valid,
        "inspector_validity_score": vr.inspector_validity_score,
        "issues": vr.issues,
        "overall_validation_confidence": vr.overall_validation_confidence,
    }
    ctx.steps_log.append({"tool": "validate_document", "result": summary})
    return json.dumps(summary)


def tool_detect_remedial_issues(ctx: OrchestratorContext, args: dict) -> str:
    """Run the remedial-detection agent on the full document text."""
    logger.info("Tool: detect_remedial_issues")
    ctx.remedial_result = run_remedial_detection_agent(ctx.document_text)
    rr = ctx.remedial_result
    summary = {
        "classification": rr.classification,
        "classification_confidence": rr.classification_confidence,
        "critical_items": rr.critical_items,
        "minor_items": rr.minor_items,
        "reasoning": rr.reasoning,
    }
    ctx.steps_log.append({"tool": "detect_remedial_issues", "result": summary})
    return json.dumps(summary, default=str)


def tool_finalize(ctx: OrchestratorContext, args: dict) -> str:
    """Record the orchestrator's final routing recommendation and stop the loop."""
    ctx.routing_decision = args["routing_decision"]
    ctx.rationale = args["rationale"]
    ctx.finalized = True
    logger.info(
        "Tool: finalize(decision=%s) – %s", ctx.routing_decision, ctx.rationale
    )
    ctx.steps_log.append({"tool": "finalize", "args": args})
    return json.dumps({"status": "finalized", "routing_decision": ctx.routing_decision})


# ── Dispatcher ────────────────────────────────────────────────────────────────

_TOOL_DISPATCH: dict = {
    "extract_all_fields": tool_extract_all_fields,
    "re_extract_field": tool_re_extract_field,
    "validate_document": tool_validate_document,
    "detect_remedial_issues": tool_detect_remedial_issues,
    "finalize": tool_finalize,
}


def dispatch_tool(name: str, args: dict, ctx: OrchestratorContext) -> str:
    """Resolve and execute a tool by name.  Returns a JSON string result."""
    fn = _TOOL_DISPATCH.get(name)
    if fn is None:
        logger.error("Unknown tool requested by LLM: %s", name)
        return json.dumps({"error": f"Unknown tool: {name}"})
    return fn(ctx, args)
