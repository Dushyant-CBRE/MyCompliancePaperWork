"""
Tests for the Agentic Orchestrator (backend/agents/orchestrator.py).

All LLM calls and agent calls are mocked so these tests run without
any Azure credentials or network access.

Three scenarios are covered:
  1. Happy path   – all fields high confidence, straight extract→validate→detect→finalize
  2. Feedback loop – site_name confidence < 60, LLM calls re_extract_field before validating
  3. Safety cap   – LLM never calls finalize, loop must hit MAX_ITERATIONS guard
"""
from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from backend.agents.orchestrator import MAX_ITERATIONS, run_orchestrator
from backend.models.document import (
    DocumentMetadata,
    ExtractedFields,
    RemedialClassification,
    RemedialResult,
    ValidationResult,
)

# ── Sample document text ──────────────────────────────────────────────────────

SAMPLE_TEXT = """\
PLANNED PREVENTIVE MAINTENANCE REPORT
Site: Canary Wharf Tower
PPM Ref: PPM-2024-001
Inspection Date: 2024-03-15
Inspector: John Smith
Equipment ID: HVAC-CW-001
Vendor: Acme Facilities Ltd
All items satisfactory. No deficiencies identified.
"""

# ── Shared agent result fixtures ──────────────────────────────────────────────

GOOD_EXTRACTED = ExtractedFields(
    site_name="Canary Wharf Tower",
    site_name_confidence=95.0,
    ppm_reference="PPM-2024-001",
    ppm_reference_confidence=98.0,
    inspection_date="2024-03-15",
    inspection_date_confidence=99.0,
    inspector_name="John Smith",
    inspector_name_confidence=97.0,
    equipment_id="HVAC-CW-001",
    equipment_id_confidence=95.0,
    document_type="HVAC",
    document_type_confidence=90.0,
    vendor_name="Acme Facilities Ltd",
    vendor_name_confidence=92.0,
    overall_extraction_confidence=95.0,
    raw_text_length=len(SAMPLE_TEXT),
)

GOOD_VALIDATION = ValidationResult(
    site_name_match=100.0,
    ppm_reference_match=100.0,
    date_valid=True,
    date_validity_score=100.0,
    inspector_valid=True,
    inspector_validity_score=100.0,
    issues=[],
    overall_validation_confidence=100.0,
)

PASS_REMEDIAL = RemedialResult(
    classification=RemedialClassification.PASS,
    classification_confidence=95.0,
    findings=["All items satisfactory"],
    critical_items=[],
    minor_items=[],
    reasoning="Document shows full compliance with no deficiencies.",
)


# ── Helper builders ───────────────────────────────────────────────────────────

def _tool_call(name: str, args: dict, call_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(name=name, arguments=json.dumps(args)),
    )


def _assistant_tool_response(*tool_calls: SimpleNamespace) -> SimpleNamespace:
    msg = SimpleNamespace(content="", role="assistant", tool_calls=list(tool_calls))
    return SimpleNamespace(choices=[SimpleNamespace(message=msg, finish_reason="tool_calls")], model="gpt4omni")


def _assistant_text_response(text: str) -> SimpleNamespace:
    """Simulates a text response (no tool_calls) – used for nudge testing."""
    msg = SimpleNamespace(content=text, role="assistant", tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg, finish_reason="stop")], model="gpt4omni")


# ── Test 1: Happy path ────────────────────────────────────────────────────────

def test_happy_path():
    """
    Straight-line flow: extract → validate → detect → finalize.
    All confidence scores are high; no re-extraction needed.
    """
    llm_sequence = [
        _assistant_tool_response(_tool_call("extract_all_fields", {}, "tc_1")),
        _assistant_tool_response(_tool_call("validate_document", {}, "tc_2")),
        _assistant_tool_response(_tool_call("detect_remedial_issues", {}, "tc_3")),
        _assistant_tool_response(_tool_call("finalize", {
            "routing_decision": "AUTO_APPROVED",
            "rationale": "High confidence extraction, perfect validation match, PASS classification.",
        }, "tc_4")),
    ]

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = llm_sequence

    with (
        patch("backend.agents.orchestrator.get_llm_client", return_value=mock_client),
        patch("backend.agents.tools.run_extraction_agent", return_value=GOOD_EXTRACTED),
        patch("backend.agents.tools.run_validation_agent", return_value=GOOD_VALIDATION),
        patch("backend.agents.tools.run_remedial_detection_agent", return_value=PASS_REMEDIAL),
    ):
        extracted, validation, remedial, state = run_orchestrator(
            document_text=SAMPLE_TEXT,
            metadata=DocumentMetadata(
                expected_site_name="Canary Wharf Tower",
                expected_ppm_reference="PPM-2024-001",
            ),
            document_id="test-happy-001",
        )

    # Agent results are passed through correctly
    assert extracted.site_name == "Canary Wharf Tower"
    assert extracted.overall_extraction_confidence == 95.0
    assert validation.overall_validation_confidence == 100.0
    assert remedial.classification == RemedialClassification.PASS

    # Orchestrator state
    assert state.iterations == 4
    assert state.orchestrator_routing == "AUTO_APPROVED"
    assert "extract_all_fields" in state.tools_called
    assert "validate_document" in state.tools_called
    assert "detect_remedial_issues" in state.tools_called
    assert "finalize" in state.tools_called
    assert len(state.steps) == 4
    assert state.final_rationale != ""


# ── Test 2: Feedback loop – low confidence triggers re-extraction ─────────────

def test_feedback_loop_re_extracts_low_confidence_field():
    """
    When site_name confidence is below 60, the LLM calls re_extract_field
    before proceeding to validation.  After re-extraction the field value
    and confidence score should be updated on the ExtractedFields object.
    """
    low_conf_extracted = ExtractedFields(
        site_name=None,
        site_name_confidence=35.0,   # below 60 – orchestrator should spot this
        ppm_reference="PPM-2024-001",
        ppm_reference_confidence=90.0,
        overall_extraction_confidence=62.0,
        raw_text_length=len(SAMPLE_TEXT),
    )

    # Sequence: extract → re_extract(site_name) → validate → detect → finalize
    orchestrator_llm_sequence = [
        _assistant_tool_response(_tool_call("extract_all_fields", {}, "tc_1")),
        _assistant_tool_response(_tool_call("re_extract_field", {
            "field_name": "site_name",
            "context_hint": "look in document header or letterhead",
        }, "tc_2")),
        _assistant_tool_response(_tool_call("validate_document", {}, "tc_3")),
        _assistant_tool_response(_tool_call("detect_remedial_issues", {}, "tc_4")),
        _assistant_tool_response(_tool_call("finalize", {
            "routing_decision": "MANUAL_REVIEW",
            "rationale": "Site name required re-extraction; medium overall confidence.",
        }, "tc_5")),
    ]

    # re_extract_field calls the LLM directly (not via orchestrator loop)
    re_extract_llm_response = SimpleNamespace(
        choices=[SimpleNamespace(
            message=SimpleNamespace(
                content=json.dumps({"value": "Canary Wharf Tower", "confidence": 88}),
                role="assistant",
                tool_calls=None,
            ),
            finish_reason="stop",
        )],
        model="gpt4omni",
    )

    # Dispatch to the right mock based on whether 'tools' kwarg is present
    orch_call_idx = 0
    def dispatch_create(*args, **kwargs):
        nonlocal orch_call_idx
        if "tools" in kwargs:
            resp = orchestrator_llm_sequence[orch_call_idx]
            orch_call_idx += 1
            return resp
        return re_extract_llm_response   # re_extract_field direct call

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = dispatch_create

    with (
        patch("backend.agents.orchestrator.get_llm_client", return_value=mock_client),
        patch("backend.agents.tools.get_llm_client", return_value=mock_client),
        patch("backend.agents.tools.run_extraction_agent", return_value=low_conf_extracted),
        patch("backend.agents.tools.run_validation_agent", return_value=GOOD_VALIDATION),
        patch("backend.agents.tools.run_remedial_detection_agent", return_value=PASS_REMEDIAL),
    ):
        extracted, validation, remedial, state = run_orchestrator(
            document_text=SAMPLE_TEXT,
            document_id="test-loop-002",
        )

    # re_extract_field should have patched the low-confidence field
    assert extracted.site_name == "Canary Wharf Tower"
    assert extracted.site_name_confidence == 88.0

    # Tool sequence recorded correctly
    assert state.tools_called == [
        "extract_all_fields",
        "re_extract_field",
        "validate_document",
        "detect_remedial_issues",
        "finalize",
    ]
    assert state.iterations == 5
    assert state.orchestrator_routing == "MANUAL_REVIEW"


# ── Test 3: MAX_ITERATIONS safety guard ──────────────────────────────────────

def test_max_iterations_safety_guard():
    """
    If the LLM never calls finalize the loop must stop at MAX_ITERATIONS
    and fall back to REQUIRES_ATTENTION.
    """
    # LLM keeps requesting validate_document indefinitely
    infinite_response = _assistant_tool_response(
        _tool_call("validate_document", {}, "tc_inf")
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = infinite_response

    with (
        patch("backend.agents.orchestrator.get_llm_client", return_value=mock_client),
        patch("backend.agents.tools.run_extraction_agent", return_value=GOOD_EXTRACTED),
        patch("backend.agents.tools.run_validation_agent", return_value=GOOD_VALIDATION),
        patch("backend.agents.tools.run_remedial_detection_agent", return_value=PASS_REMEDIAL),
    ):
        extracted, validation, remedial, state = run_orchestrator(
            document_text=SAMPLE_TEXT,
            document_id="test-cap-003",
        )

    assert state.iterations == MAX_ITERATIONS
    assert state.orchestrator_routing == "REQUIRES_ATTENTION"
    assert "iteration limit" in state.final_rationale.lower()


# ── Test 4: Nudge when LLM returns text instead of a tool call ───────────────

def test_nudge_when_no_tool_call():
    """
    If the LLM returns plain text on first turn, the orchestrator should
    nudge it and eventually get back on track.
    """
    llm_sequence = [
        _assistant_text_response("I will now extract the fields."),   # nudge needed
        _assistant_tool_response(_tool_call("extract_all_fields", {}, "tc_1")),
        _assistant_tool_response(_tool_call("validate_document", {}, "tc_2")),
        _assistant_tool_response(_tool_call("detect_remedial_issues", {}, "tc_3")),
        _assistant_tool_response(_tool_call("finalize", {
            "routing_decision": "AUTO_APPROVED",
            "rationale": "All checks passed.",
        }, "tc_4")),
    ]

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = llm_sequence

    with (
        patch("backend.agents.orchestrator.get_llm_client", return_value=mock_client),
        patch("backend.agents.tools.run_extraction_agent", return_value=GOOD_EXTRACTED),
        patch("backend.agents.tools.run_validation_agent", return_value=GOOD_VALIDATION),
        patch("backend.agents.tools.run_remedial_detection_agent", return_value=PASS_REMEDIAL),
    ):
        extracted, validation, remedial, state = run_orchestrator(
            document_text=SAMPLE_TEXT,
            document_id="test-nudge-004",
        )

    assert state.orchestrator_routing == "AUTO_APPROVED"
    # nudge iteration + 4 tool iterations = 5
    assert state.iterations == 5
    assert "finalize" in state.tools_called
