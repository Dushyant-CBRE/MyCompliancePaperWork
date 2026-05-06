"""
Pydantic data models shared across the application.
"""
from __future__ import annotations
from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Enumerations ─────────────────────────────────────────────────────────────

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    AUTO_APPROVED = "auto_approved"
    MANUAL_REVIEW = "manual_review"
    REQUIRES_ATTENTION = "requires_attention"
    APPROVED = "approved"       # Officer manually approved
    REJECTED = "rejected"       # Officer manually rejected


class RemedialClassification(str, Enum):
    PASS = "PASS"
    REMEDIAL_MINOR = "REMEDIAL_MINOR"
    REMEDIAL_CRITICAL = "REMEDIAL_CRITICAL"
    UNKNOWN = "UNKNOWN"


# ── Agent output models ───────────────────────────────────────────────────────

class ExtractedFields(BaseModel):
    """Output from Agent 1 – Extraction Agent."""
    site_name: Optional[str] = None
    site_name_confidence: float = 0.0
    site_name_source: Optional[str] = None           # verbatim sentence it was found in

    ppm_reference: Optional[str] = None
    ppm_reference_confidence: float = 0.0
    ppm_reference_source: Optional[str] = None

    inspection_date: Optional[str] = None
    inspection_date_confidence: float = 0.0
    inspection_date_source: Optional[str] = None

    inspector_name: Optional[str] = None
    inspector_name_confidence: float = 0.0
    inspector_name_source: Optional[str] = None

    equipment_id: Optional[str] = None
    equipment_id_confidence: float = 0.0
    equipment_id_source: Optional[str] = None

    document_type: Optional[str] = None
    document_type_confidence: float = 0.0
    document_type_source: Optional[str] = None

    vendor_name: Optional[str] = None
    vendor_name_confidence: float = 0.0
    vendor_name_source: Optional[str] = None

    # ── Extended fields ───────────────────────────────────────────────────────
    certificate_number: Optional[str] = None
    certificate_number_confidence: float = 0.0
    certificate_number_source: Optional[str] = None

    next_service_date: Optional[str] = None          # ISO 8601
    next_service_date_confidence: float = 0.0
    next_service_date_source: Optional[str] = None

    overall_outcome: Optional[str] = None            # e.g. "Satisfactory", "Failed"
    overall_outcome_confidence: float = 0.0
    overall_outcome_source: Optional[str] = None

    page_count: Optional[int] = None                 # total pages in document
    client_name: Optional[str] = None                # building owner / client
    client_name_confidence: float = 0.0
    client_name_source: Optional[str] = None

    # Key readings / measurements extracted verbatim (e.g. chemical levels)
    key_readings: list[dict] = Field(default_factory=list)   # [{name, value, unit, status}]

    overall_extraction_confidence: float = 0.0
    raw_text_length: int = 0


class ValidationResult(BaseModel):
    """Output from Agent 2 – Validation Agent."""
    site_name_match: float = 0.0       # 0-100 match score
    ppm_reference_match: float = 0.0
    date_valid: bool = False
    date_validity_score: float = 0.0
    inspector_valid: bool = False
    inspector_validity_score: float = 0.0
    issues: list[str] = Field(default_factory=list)
    overall_validation_confidence: float = 0.0
    # Structured pass/fail checks surfaced in the Review UI
    # Each item: {check: str, status: "pass"|"fail", detail: str}
    checks: list[dict] = Field(default_factory=list)


class RemedialResult(BaseModel):
    """Output from Agent 3 – Remedial Detection Agent."""
    classification: RemedialClassification = RemedialClassification.UNKNOWN
    classification_confidence: float = 0.0
    findings: list[str] = Field(default_factory=list)
    critical_items: list[str] = Field(default_factory=list)
    minor_items: list[str] = Field(default_factory=list)
    reasoning: str = ""
    # Structured evidence list surfaced in the Review UI
    # Each item: {text: str, page: int, severity: "High"|"Medium"|"Low"}
    evidence: list[dict] = Field(default_factory=list)


# ── Orchestrator / Agentic loop models ────────────────────────────────────────

class OrchestratorStep(BaseModel):
    """Records one tool invocation in the orchestrator's agentic loop."""
    iteration: int
    tool_name: str
    tool_args: dict = Field(default_factory=dict)
    result_summary: str = ""


class AgentState(BaseModel):
    """
    Shared memory maintained across the orchestrator's agentic loop.
    Captures the full decision trail so the audit log can replay it.
    """
    iterations: int = 0
    steps: list[OrchestratorStep] = Field(default_factory=list)
    tools_called: list[str] = Field(default_factory=list)
    final_rationale: str = ""
    orchestrator_routing: Optional[str] = None   # routing decision suggested by LLM


class ConfidenceScore(BaseModel):
    """Weighted confidence score and routing decision."""
    extraction_score: float = 0.0
    validation_score: float = 0.0
    remedial_score: float = 0.0
    overall_score: float = 0.0
    decision: DocumentStatus = DocumentStatus.REQUIRES_ATTENTION


# ── Insights model (computed, not from LLM) ───────────────────────────────────

class DocumentInsights(BaseModel):
    """
    High-level insights derived from all three agent outputs.
    Computed deterministically — no extra LLM call needed.
    Surfaced to the frontend for the review panel.
    """
    # Compliance summary
    compliance_status: str = "Unknown"          # "Compliant" | "Non-Compliant" | "Advisory"
    risk_level: str = "Unknown"                 # "Low" | "Medium" | "High" | "Critical"
    days_until_next_service: Optional[int] = None
    is_overdue: bool = False

    # Field completeness
    fields_extracted: int = 0
    fields_total: int = 9                       # all expected fields
    completeness_pct: float = 0.0

    # Key flags surfaced for the officer
    flags: list[str] = Field(default_factory=list)

    # SLA countdown string for the Review header (e.g. "4h 23m", "Overdue")
    sla_remaining: Optional[str] = None

    # Confidence breakdown for sparkline / radar chart
    score_breakdown: list[dict] = Field(default_factory=list)  # [{label, score, weight}]


# ── Document models ───────────────────────────────────────────────────────────

class DocumentMetadata(BaseModel):
    """Metadata supplied at upload time."""
    expected_site_name: Optional[str] = None
    expected_ppm_type: Optional[str] = None
    expected_document_date: Optional[datetime] = None
    expected_document_type: Optional[str] = None
    expected_vendor_name: Optional[str] = None
    notes: Optional[str] = None


class DocumentRecord(BaseModel):
    """Full document record stored in Table Storage."""
    document_id: str
    filename: str
    blob_url: Optional[str] = None
    status: DocumentStatus = DocumentStatus.PENDING
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None

    metadata: Optional[DocumentMetadata] = None
    extracted_fields: Optional[ExtractedFields] = None
    validation_result: Optional[ValidationResult] = None
    remedial_result: Optional[RemedialResult] = None
    confidence_score: Optional[ConfidenceScore] = None
    agent_state: Optional[AgentState] = None
    insights: Optional[DocumentInsights] = None

    # Officer override
    override_by: Optional[str] = None
    override_reason: Optional[str] = None
    overridden_at: Optional[datetime] = None


# ── API request / response models ────────────────────────────────────────────

class OverrideRequest(BaseModel):
    decision: DocumentStatus
    reason: str
    officer_name: str


class ReviewRequest(BaseModel):
    """Payload for an officer review submission."""
    status: str                        # "Approved" or "Rejected"
    justification: str


class ReviewResponse(BaseModel):
    """Response returned after a review is submitted."""
    document_id: str
    status: DocumentStatus
    justification: str
    reviewed_at: datetime


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    message: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentRecord]
    total: int


class AnalyticsSummary(BaseModel):
    total_documents: int = 0
    auto_approved: int = 0
    manual_review: int = 0
    requires_attention: int = 0
    approved: int = 0
    rejected: int = 0
    avg_confidence: float = 0.0
    remedial_pass: int = 0
    remedial_minor: int = 0
    remedial_critical: int = 0
    auto_approval_rate: float = 0.0
    avg_processing_time_seconds: float = 0.0
    # Chart data
    processing_buckets: list[dict] = Field(default_factory=list)     # [{time, count}]
    confidence_distribution: list[dict] = Field(default_factory=list) # [{range, count}]
    site_breakdown: list[dict] = Field(default_factory=list)          # [{site, approved, review, remedial}]
    ppm_distribution: list[dict] = Field(default_factory=list)        # [{type, count}]


# ── Reviewer Q&A (RAG) models ─────────────────────────────────────────────────

class CitedChunk(BaseModel):
    """A passage from the original document cited as evidence for an answer."""
    chunk_index: int
    text: str
    relevance_score: float = 0.0   # 0-1 keyword overlap score


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[CitedChunk] = Field(default_factory=list)
    document_id: str


# ── Dashboard models ──────────────────────────────────────────────────────────

class DashboardDocumentSummary(BaseModel):
    """Lightweight document summary for the dashboard table/feed."""
    document_id: str
    filename: str
    status: DocumentStatus
    site_name: Optional[str] = None
    document_type: Optional[str] = None
    inspection_date: Optional[str] = None
    next_service_date: Optional[str] = None
    overall_confidence: Optional[float] = None
    remedial_classification: Optional[str] = None
    compliance_status: Optional[str] = None
    risk_level: Optional[str] = None
    is_overdue: bool = False
    uploaded_at: datetime
    processed_at: Optional[datetime] = None


class DashboardResponse(BaseModel):
    """Aggregated dashboard data loaded directly from Azure Table Storage."""
    # ── KPI counters ──────────────────────────────────────────────────────────
    total_documents: int = 0
    pending: int = 0
    processing: int = 0
    auto_approved: int = 0
    manual_review: int = 0
    requires_attention: int = 0
    approved: int = 0
    rejected: int = 0

    # ── Compliance / quality stats ────────────────────────────────────────────
    avg_confidence: float = 0.0
    overdue_count: int = 0
    remedial_pass: int = 0
    remedial_minor: int = 0
    remedial_critical: int = 0

    # ── Document feeds ────────────────────────────────────────────────────────
    recent_documents: list[DashboardDocumentSummary] = Field(default_factory=list)
    attention_documents: list[DashboardDocumentSummary] = Field(default_factory=list)