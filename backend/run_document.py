"""
Quick end-to-end runner – drop a PDF in and see the agentic pipeline work.

Usage:
    python -m backend.run_document path/to/document.pdf
    python -m backend.run_document path/to/document.pdf --site "Canary Wharf" --ppm "PPM-001"

Skips blob/table storage so no Azure Storage connection is needed.
Only the LLM (WSO2/OpenAI) credentials in .env are required.

Output is plain text to stdout — the real consumer is the React frontend via FastAPI.
"""
from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path


def _hr(title: str = ""):
    print(f"\n{'─' * 60} {title}")


def _section(label: str, value):
    print(f"  {label}: {value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the agentic compliance pipeline on a PDF.")
    parser.add_argument("pdf", type=Path, help="Path to the PDF document")
    parser.add_argument("--site",     default=None, help="Expected site name")
    parser.add_argument("--ppm",      default=None, help="Expected PPM reference")
    parser.add_argument("--doctype",  default=None, help="Expected document type")
    parser.add_argument("--officer",  default="test-run", help="Submitted by (default: test-run)")
    args = parser.parse_args()

    if not args.pdf.exists():
        print(f"File not found: {args.pdf}")
        sys.exit(1)

    pdf_bytes = args.pdf.read_bytes()
    _hr("My Compliance Paperwork – Agentic Pipeline")
    print(f"  Document : {args.pdf.name}  ({len(pdf_bytes):,} bytes)")

    # ── Step 1: Extract text ──────────────────────────────────────────────────
    _hr("Step 1 – PDF Text Extraction")
    from backend.services.pdf_extractor import extract_text_from_pdf
    document_text = extract_text_from_pdf(pdf_bytes)
    print(f"  Extracted {len(document_text):,} characters")
    preview = document_text[:400].replace("\n", " ")
    print(f"  Preview : {textwrap.shorten(preview, 120)}")

    # ── Step 2: Build metadata ────────────────────────────────────────────────
    from backend.models.document import DocumentMetadata
    metadata = DocumentMetadata(
        expected_site_name=args.site,
        expected_ppm_reference=args.ppm,
        expected_document_type=args.doctype,
        submitted_by=args.officer,
    )
    if any([args.site, args.ppm, args.doctype]):
        _hr("Expected Metadata")
        if args.site:    _section("Expected site",     args.site)
        if args.ppm:     _section("Expected PPM ref",  args.ppm)
        if args.doctype: _section("Expected doc type", args.doctype)

    # ── Step 3: Run orchestrator ──────────────────────────────────────────────
    _hr("Step 2 – Agentic Orchestrator (LLM tool-use loop)")
    print("  Connecting to CBRE WSO2 API Gateway …\n")

    from backend.agents.orchestrator import run_orchestrator
    extracted, validation, remedial, agent_state = run_orchestrator(
        document_text=document_text,
        metadata=metadata,
        document_id=args.pdf.stem,
    )

    # ── Print orchestrator trace ──────────────────────────────────────────────
    _hr("Orchestrator Trace")
    for step in agent_state.steps:
        print(f"  Iter {step.iteration:>2}  {step.tool_name:<28}  {textwrap.shorten(step.result_summary, 80)}")

    print(f"\n  Total iterations : {agent_state.iterations}")
    print(f"  LLM routing hint : {agent_state.orchestrator_routing}")
    print(f"  Rationale        : {textwrap.shorten(agent_state.final_rationale, 100)}")

    # ── Extracted fields ──────────────────────────────────────────────────────
    _hr("Extracted Fields")
    fields = [
        ("Site name",       extracted.site_name,       extracted.site_name_confidence),
        ("PPM reference",   extracted.ppm_reference,   extracted.ppm_reference_confidence),
        ("Inspection date", extracted.inspection_date, extracted.inspection_date_confidence),
        ("Inspector name",  extracted.inspector_name,  extracted.inspector_name_confidence),
        ("Equipment ID",    extracted.equipment_id,    extracted.equipment_id_confidence),
        ("Document type",   extracted.document_type,   extracted.document_type_confidence),
        ("Vendor name",     extracted.vendor_name,     extracted.vendor_name_confidence),
    ]
    for label, value, conf in fields:
        print(f"  {label:<18} {str(value or 'null'):<35} {conf:.0f}%")
    print(f"\n  Overall extraction confidence : {extracted.overall_extraction_confidence:.1f}%")

    # ── Validation results ────────────────────────────────────────────────────
    _hr("Validation Results")
    _section("Site match",         f"{validation.site_name_match:.0f}%")
    _section("PPM ref match",      f"{validation.ppm_reference_match:.0f}%")
    _section("Date valid",         validation.date_valid)
    _section("Inspector valid",    validation.inspector_valid)
    _section("Overall validation", f"{validation.overall_validation_confidence:.1f}%")
    if validation.issues:
        print("  Issues:")
        for issue in validation.issues:
            print(f"    - {issue}")

    # ── Remedial classification ───────────────────────────────────────────────
    _hr("Remedial Classification")
    print(f"  Classification : {remedial.classification.value}  ({remedial.classification_confidence:.0f}% confidence)")
    print(f"  Reasoning      : {textwrap.shorten(remedial.reasoning, 100)}")
    if remedial.critical_items:
        print("  Critical items:")
        for item in remedial.critical_items:
            print(f"    ! {item}")
    if remedial.minor_items:
        print("  Minor items:")
        for item in remedial.minor_items:
            print(f"    - {item}")

    # ── Final confidence score + routing ─────────────────────────────────────
    from backend.services.confidence_scorer import calculate_confidence
    score = calculate_confidence(extracted, validation, remedial)

    _hr("Final Decision")
    print(f"\n  ROUTING DECISION : {score.decision.value.upper()}")
    print(f"  Extraction score : {score.extraction_score:.1f}%  (weight 30%)")
    print(f"  Validation score : {score.validation_score:.1f}%  (weight 30%)")
    print(f"  Remedial score   : {score.remedial_score:.1f}%  (weight 40%)")
    print(f"  Overall score    : {score.overall_score:.1f}%")
    print()


if __name__ == "__main__":
    main()
