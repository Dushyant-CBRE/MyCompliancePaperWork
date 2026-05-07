"""
Orchestrator Agent  –  True Agentic Loop
─────────────────────────────────────────
Replaces the hardcoded linear pipeline with a genuine agentic loop where the
LLM autonomously decides:

  • Which tools to call (and in what order)
  • Whether to loop back and re-extract low-confidence fields
  • When enough evidence has been gathered to finalize

Agentic properties implemented
───────────────────────────────
  ✓ Tool use       — LLM calls structured tools via OpenAI function-calling
  ✓ Planning       — LLM decides which tool to invoke next based on results
  ✓ Feedback loops — low confidence → re_extract_field → re-validate
  ✓ Memory         — full conversation history accumulates across tool calls
  ✓ Replanning     — orchestrator may change strategy when intermediate
                     results reveal unexpected issues
  ✓ Safety guard   — hard cap of MAX_ITERATIONS to prevent runaway loops
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from backend.agents.critic_agent import CriticFeedback, run_critic
from backend.agents.tools import TOOL_SCHEMAS, OrchestratorContext, dispatch_tool
from backend.config import get_settings
from backend.models.document import (
    AgentState,
    DocumentMetadata,
    ExtractedFields,
    OrchestratorStep,
    RemedialResult,
    ValidationResult,
)
from backend.utils.llm_client import get_llm_client

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 10   # hard safety cap on agentic loop iterations

_SYSTEM_PROMPT = """\
You are an autonomous compliance document processing orchestrator.
Your goal is to accurately process a PPM (Planned Preventive Maintenance) \
compliance document and make a justified routing decision.

You have five tools:

1. extract_all_fields   — Run first. Extracts all structured fields with confidence scores.
2. re_extract_field     — Re-extract a specific field with a targeted hint.
                          Use when a field confidence score is below 60, or when
                          a validation match score is below 50.
3. validate_document    — Cross-check extracted fields against expected metadata.
                          Call after extraction (and any re-extractions).
4. detect_remedial_issues — Classify the document: PASS / REMEDIAL_MINOR / REMEDIAL_CRITICAL.
                            Call after validation.
5. finalize             — Record your final routing recommendation.
                          MUST be called once all required tools have been run.

Decision strategy
─────────────────
- Extract → Validate → Detect remedial issues → Finalize.
- If site_name or ppm_reference confidence < 60, use re_extract_field before validating.
- If validation reveals site_name_match or ppm_reference_match < 50, re-extract that field.
- A REMEDIAL_CRITICAL finding MUST result in at least MANUAL_REVIEW.
- Overall confidence < 60 → REQUIRES_ATTENTION.
- Overall confidence 60–85 → MANUAL_REVIEW.
- Overall confidence ≥ 85 with PASS remedial → AUTO_APPROVED.

You MUST call finalize() to complete processing.
"""


def run_orchestrator(
    document_text: str,
    metadata: Optional[DocumentMetadata] = None,
    document_id: str = "unknown",
    pre_extracted_fields: Optional[ExtractedFields] = None,
) -> tuple[ExtractedFields, ValidationResult, RemedialResult, AgentState]:
    """
    Run the agentic orchestration loop for one document.

    Parameters
    ----------
    pre_extracted_fields : If provided (from Content Understanding custom analyzer),
                           Agent 1 (extract_all_fields) is skipped and these fields
                           are injected directly into the orchestrator context so the
                           loop starts from validation.

    Returns
    -------
    (ExtractedFields, ValidationResult, RemedialResult, AgentState)
    The caller (document_processor) uses these to compute the final confidence
    score and persist the full record.
    """
    settings = get_settings()
    client = get_llm_client()

    ctx = OrchestratorContext(document_text=document_text, metadata=metadata)

    # ── Inject pre-extracted fields from Content Understanding ───────────────
    if pre_extracted_fields is not None:
        ctx.extracted_fields = pre_extracted_fields
        logger.info(
            "[%s] Skipping Agent 1 — using Content Understanding fields "
            "(overall confidence %.1f%%)",
            document_id,
            pre_extracted_fields.overall_extraction_confidence,
        )

    # ── Build initial user message ────────────────────────────────────────────
    metadata_str = "None provided."
    if metadata:
        metadata_str = json.dumps({
            "expected_site_name":     metadata.expected_site_name,
            "expected_ppm_type":      getattr(metadata, "expected_ppm_type", None),
            "expected_document_type": metadata.expected_document_type,
            "expected_vendor_name":   getattr(metadata, "expected_vendor_name", None),
        })

    # Truncate document preview for the system message (full text goes to tools)
    doc_preview = document_text[:800] + ("…[truncated]" if len(document_text) > 800 else "")

    # Tell the orchestrator what to start with
    if pre_extracted_fields is not None:
        first_instruction = (
            "Fields have already been extracted by Azure AI Content Understanding "
            f"with overall confidence {pre_extracted_fields.overall_extraction_confidence:.0f}%. "
            "Skip extract_all_fields and begin with validate_document."
        )
    else:
        first_instruction = "Begin by calling extract_all_fields."

    messages: list[dict] = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Process the following compliance document.\n\n"
                f"Expected metadata: {metadata_str}\n\n"
                f"Document preview (first 800 chars):\n{doc_preview}\n\n"
                f"{first_instruction}"
            ),
        },
    ]

    agent_state = AgentState()
    iteration = 0

    # ── Agentic loop ─────────────────────────────────────────────────────────
    while not ctx.finalized and iteration < MAX_ITERATIONS:
        iteration += 1
        logger.info("[%s] Orchestrator iteration %d", document_id, iteration)

        response = client.chat.completions.create(
            model=settings.azure_openai_deployment_primary,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=0.0,
        )

        choice = response.choices[0]
        assistant_message = choice.message

        # Append assistant turn to conversation memory
        tool_calls = assistant_message.tool_calls
        messages.append({
            "role": "assistant",
            "content": assistant_message.content or "",
            **({"tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in tool_calls
            ]} if tool_calls else {}),
        })

        if not tool_calls:
            # LLM gave a text response instead of a tool call – nudge it
            logger.warning(
                "[%s] Orchestrator: no tool_calls in response (iteration %d) – nudging",
                document_id,
                iteration,
            )
            messages.append({
                "role": "user",
                "content": (
                    "You must call a tool. If you have finished, call finalize(). "
                    "If you haven't extracted fields yet, call extract_all_fields()."
                ),
            })
            continue

        # ── Execute each tool call the LLM requested ──────────────────────
        for tc in tool_calls:
            tool_name = tc.function.name
            try:
                tool_args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                tool_args = {}

            logger.info("[%s] Calling tool: %s(args=%s)", document_id, tool_name, tool_args)
            tool_result = dispatch_tool(tool_name, tool_args, ctx)

            # Record step in audit trail
            agent_state.steps.append(
                OrchestratorStep(
                    iteration=iteration,
                    tool_name=tool_name,
                    tool_args=tool_args,
                    result_summary=tool_result[:300],  # cap stored summary
                )
            )
            agent_state.tools_called.append(tool_name)

            # Return tool result to the LLM as a tool message
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": tool_result,
            })

    # ── Loop ended ────────────────────────────────────────────────────────────
    if not ctx.finalized:
        logger.warning(
            "[%s] Orchestrator hit MAX_ITERATIONS (%d) without finalizing – "
            "falling back to REQUIRES_ATTENTION",
            document_id,
            MAX_ITERATIONS,
        )
        ctx.routing_decision = "REQUIRES_ATTENTION"
        ctx.rationale = f"Orchestrator reached iteration limit ({MAX_ITERATIONS}) without a confident decision."

    agent_state.iterations = iteration
    agent_state.final_rationale = ctx.rationale
    agent_state.orchestrator_routing = ctx.routing_decision

    # ── Critic / self-reflection pass ─────────────────────────────────────────
    # Only run critic when both remedial AND validation tools have fired,
    # i.e., there is meaningful output to review.
    extracted_final = ctx.extracted_fields or ExtractedFields(raw_text_length=len(document_text))
    validation_final = ctx.validation_result or ValidationResult()
    remedial_final   = ctx.remedial_result or RemedialResult()

    ran_remedial = "detect_remedial_issues" in agent_state.tools_called
    ran_validate = "validate_document" in agent_state.tools_called

    if ran_remedial and ran_validate:
        try:
            critic_feedback: CriticFeedback = run_critic(
                document_text=document_text,
                extracted_fields=extracted_final.dict() if hasattr(extracted_final, "dict") else {},
                validation_result=validation_final.dict() if hasattr(validation_final, "dict") else {},
                remedial_result=remedial_final.dict() if hasattr(remedial_final, "dict") else {},
            )

            agent_state.tools_called.append("critic_review")
            agent_state.steps.append(
                OrchestratorStep(
                    iteration=iteration + 1,
                    tool_name="critic_review",
                    tool_args={},
                    result_summary=(
                        f"agreed={critic_feedback.agreed}, "
                        f"concerns={len(critic_feedback.concerns)}, "
                        f"delta={critic_feedback.confidence_delta:+.2f}, "
                        f"revised_classification={critic_feedback.revised_classification}"
                    ),
                )
            )

            if not critic_feedback.agreed:
                logger.info(
                    "[%s] Critic DISAGREES — concerns: %s",
                    document_id,
                    critic_feedback.concerns,
                )
                # Escalate classification if critic demands it
                if critic_feedback.revised_classification in ("REMEDIAL", "REMEDIAL_CRITICAL"):
                    if ctx.routing_decision == "AUTO_APPROVED":
                        ctx.routing_decision = "MANUAL_REVIEW"
                        ctx.rationale = (
                            f"Critic escalated from AUTO_APPROVED to MANUAL_REVIEW. "
                            f"Concerns: {'; '.join(critic_feedback.concerns)}"
                        )
                # Apply confidence delta
                if critic_feedback.confidence_delta != 0.0 and extracted_final:
                    old_conf = extracted_final.overall_extraction_confidence
                    extracted_final.overall_extraction_confidence = max(
                        0.0,
                        min(100.0, old_conf + critic_feedback.confidence_delta * 100),
                    )
                    logger.info(
                        "[%s] Critic confidence adjustment: %.1f → %.1f",
                        document_id,
                        old_conf,
                        extracted_final.overall_extraction_confidence,
                    )

                # Append critic concerns to rationale
                if critic_feedback.concerns:
                    ctx.rationale = (
                        f"{ctx.rationale} | Critic concerns: "
                        + "; ".join(critic_feedback.concerns)
                    )
            else:
                logger.info("[%s] Critic AGREES with agent analysis.", document_id)

            agent_state.final_rationale = ctx.rationale
            agent_state.orchestrator_routing = ctx.routing_decision

        except Exception as exc:
            logger.warning("[%s] Critic agent raised unexpected error (skipped): %s", document_id, exc)

    logger.info(
        "[%s] Orchestrator complete: %d iterations, tools=%s, routing=%s",
        document_id,
        iteration,
        agent_state.tools_called,
        ctx.routing_decision,
    )

    # ── Return agent results (falling back to empty models if a tool never ran) ──
    return extracted_final, validation_final, remedial_final, agent_state
