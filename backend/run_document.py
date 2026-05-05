"""
Quick end-to-end runner – drop a PDF in and see the agentic pipeline work.

Usage:
    python -m backend.run_document path/to/document.pdf
    python -m backend.run_document path/to/document.pdf --site "Canary Wharf" --ppm "PPM-001"
    python -m backend.run_document path/to/document.pdf --json          # machine-readable output
    python -m backend.run_document path/to/document.pdf --json > out.json

Skips blob/table storage so no Azure Storage connection is needed.
Only the LLM (WSO2/OpenAI) credentials in .env are required.
"""
from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path


_json_mode = False


def _hr(title: str = ""):
    print(f"\n{'-' * 60} {title}", file=sys.stderr if _json_mode else sys.stdout)


def _log(*args, **kwargs):
    """Print to stderr in --json mode, stdout otherwise."""
    kwargs.setdefault("file", sys.stderr if _json_mode else sys.stdout)
    print(*args, **kwargs)


def _section(label: str, value):
    _log(f"  {label}: {value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the agentic compliance pipeline on a PDF.")
    parser.add_argument("pdf", type=Path, help="Path to the PDF document")
    parser.add_argument("--site",     default=None, help="Expected site name")
    parser.add_argument("--ppm",      default=None, help="Expected PPM type")
    parser.add_argument("--doctype",  default=None, help="Expected document type")
    parser.add_argument("--officer",  default="test-run", help="Submitted by (default: test-run)")
    parser.add_argument("--json",     action="store_true", help="Output machine-readable JSON instead of plain text")
    args = parser.parse_args()

    if not args.pdf.exists():
        print(f"File not found: {args.pdf}")
        sys.exit(1)

    global _json_mode
    _json_mode = args.json

    pdf_bytes = args.pdf.read_bytes()
    _hr("My Compliance Paperwork – Agentic Pipeline")
    _log(f"  Document : {args.pdf.name}  ({len(pdf_bytes):,} bytes)")

    # ── Step 1: Extract text ──────────────────────────────────────────────────
    _hr("Step 1 – PDF Text Extraction")
    from backend.services.pdf_extractor import extract_text_from_pdf
    document_text = extract_text_from_pdf(pdf_bytes)
    _log(f"  Extracted {len(document_text):,} characters")
    preview = document_text[:400].replace("\n", " ")
    _log(f"  Preview : {textwrap.shorten(preview, 120)}")

    # ── Step 2: Build metadata ────────────────────────────────────────────────
    from backend.models.document import DocumentMetadata
    metadata = DocumentMetadata(
        expected_site_name=args.site,
        expected_ppm_type=args.ppm,
        expected_document_type=args.doctype,
    )
    if any([args.site, args.ppm, args.doctype]):
        _hr("Expected Metadata")
        if args.site:    _section("Expected site",     args.site)
        if args.ppm:     _section("Expected PPM ref",  args.ppm)
        if args.doctype: _section("Expected doc type", args.doctype)

    # ── Step 3: Run orchestrator ──────────────────────────────────────────────
    if not args.json:
        _hr("Step 2 – Agentic Orchestrator (LLM tool-use loop)")
        _log("  Connecting to CBRE WSO2 API Gateway ...\n")
    else:
        print("Running orchestrator...", file=sys.stderr)

    from backend.agents.orchestrator import run_orchestrator
    from backend.services.confidence_scorer import calculate_confidence
    from backend.services.insights_service import generate_insights

    extracted, validation, remedial, agent_state = run_orchestrator(
        document_text=document_text,
        metadata=metadata,
        document_id=args.pdf.stem,
    )
    score = calculate_confidence(extracted, validation, remedial)
    insights = generate_insights(extracted, validation, remedial, score)

    # ── JSON output ───────────────────────────────────────────────────────────
    if args.json:
        output = {
            "document": args.pdf.name,
            "routing_decision": score.decision.value,
            "confidence": {
                "overall": round(score.overall_score, 1),
                "extraction": round(score.extraction_score, 1),
                "validation": round(score.validation_score, 1),
                "remedial": round(score.remedial_score, 1),
            },
            "extracted_fields": {
                "site_name":                   extracted.site_name,
                "site_name_confidence":         extracted.site_name_confidence,
                "site_name_source":             extracted.site_name_source,
                "ppm_reference":                extracted.ppm_reference,
                "ppm_reference_confidence":     extracted.ppm_reference_confidence,
                "ppm_reference_source":         extracted.ppm_reference_source,
                "inspection_date":              extracted.inspection_date,
                "inspection_date_confidence":   extracted.inspection_date_confidence,
                "inspection_date_source":       extracted.inspection_date_source,
                "inspector_name":               extracted.inspector_name,
                "inspector_name_confidence":    extracted.inspector_name_confidence,
                "inspector_name_source":        extracted.inspector_name_source,
                "equipment_id":                 extracted.equipment_id,
                "equipment_id_confidence":      extracted.equipment_id_confidence,
                "equipment_id_source":          extracted.equipment_id_source,
                "document_type":                extracted.document_type,
                "document_type_confidence":     extracted.document_type_confidence,
                "document_type_source":         extracted.document_type_source,
                "vendor_name":                  extracted.vendor_name,
                "vendor_name_confidence":       extracted.vendor_name_confidence,
                "vendor_name_source":           extracted.vendor_name_source,
                "certificate_number":           extracted.certificate_number,
                "certificate_number_confidence": extracted.certificate_number_confidence,
                "certificate_number_source":    extracted.certificate_number_source,
                "next_service_date":            extracted.next_service_date,
                "next_service_date_confidence": extracted.next_service_date_confidence,
                "next_service_date_source":     extracted.next_service_date_source,
                "overall_outcome":              extracted.overall_outcome,
                "overall_outcome_confidence":   extracted.overall_outcome_confidence,
                "overall_outcome_source":       extracted.overall_outcome_source,
                "client_name":                  extracted.client_name,
                "client_name_confidence":       extracted.client_name_confidence,
                "client_name_source":           extracted.client_name_source,
                "key_readings":          extracted.key_readings,
                "overall_extraction_confidence": extracted.overall_extraction_confidence,
            },
            "validation": {
                "site_name_match":              validation.site_name_match,
                "ppm_reference_match":          validation.ppm_reference_match,
                "date_valid":                   validation.date_valid,
                "date_validity_score":          validation.date_validity_score,
                "inspector_valid":              validation.inspector_valid,
                "inspector_validity_score":     validation.inspector_validity_score,
                "issues":                       validation.issues,
                "overall_validation_confidence": validation.overall_validation_confidence,
            },
            "remedial": {
                "classification":            remedial.classification.value,
                "classification_confidence": remedial.classification_confidence,
                "findings":                  remedial.findings,
                "critical_items":            remedial.critical_items,
                "minor_items":               remedial.minor_items,
                "reasoning":                 remedial.reasoning,
            },
            "insights": {
                "compliance_status":       insights.compliance_status,
                "risk_level":              insights.risk_level,
                "days_until_next_service": insights.days_until_next_service,
                "is_overdue":              insights.is_overdue,
                "fields_extracted":        insights.fields_extracted,
                "fields_total":            insights.fields_total,
                "completeness_pct":        insights.completeness_pct,
                "flags":                   insights.flags,
                "score_breakdown":         insights.score_breakdown,
            },
            "orchestrator": {
                "iterations":         agent_state.iterations,
                "tools_called":       agent_state.tools_called,
                "routing_hint":       agent_state.orchestrator_routing,
                "rationale":          agent_state.final_rationale,
            },
        }
        print(json.dumps(output, indent=2, default=str))
        return

    # ── Plain-text output ─────────────────────────────────────────────────────
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
    _hr("Final Decision")
    print(f"\n  ROUTING DECISION : {score.decision.value.upper()}")
    print(f"  Extraction score : {score.extraction_score:.1f}%  (weight 30%)")
    print(f"  Validation score : {score.validation_score:.1f}%  (weight 30%)")
    print(f"  Remedial score   : {score.remedial_score:.1f}%  (weight 40%)")
    print(f"  Overall score    : {score.overall_score:.1f}%")
    print()


if __name__ == "__main__":
    main()
