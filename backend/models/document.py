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

    ppm_reference: Optional[str] = None
    ppm_reference_confidence: float = 0.0

    inspection_date: Optional[str] = None
    inspection_date_confidence: float = 0.0

    inspector_name: Optional[str] = None
    inspector_name_confidence: float = 0.0

    equipment_id: Optional[str] = None
    equipment_id_confidence: float = 0.0

    document_type: Optional[str] = None
    document_type_confidence: float = 0.0

    vendor_name: Optional[str] = None
    vendor_name_confidence: float = 0.0

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


class RemedialResult(BaseModel):
    """Output from Agent 3 – Remedial Detection Agent."""
    classification: RemedialClassification = RemedialClassification.UNKNOWN
    classification_confidence: float = 0.0
    findings: list[str] = Field(default_factory=list)
    critical_items: list[str] = Field(default_factory=list)
    minor_items: list[str] = Field(default_factory=list)
    reasoning: str = ""


class ConfidenceScore(BaseModel):
    """Weighted confidence score and routing decision."""
    extraction_score: float = 0.0
    validation_score: float = 0.0
    remedial_score: float = 0.0
    overall_score: float = 0.0
    decision: DocumentStatus = DocumentStatus.REQUIRES_ATTENTION


# ── Document models ───────────────────────────────────────────────────────────

class DocumentMetadata(BaseModel):
    """Metadata supplied at upload time."""
    expected_site_name: Optional[str] = None
    expected_ppm_reference: Optional[str] = None
    expected_document_type: Optional[str] = None
    submitted_by: Optional[str] = None
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

    # Officer override
    override_by: Optional[str] = None
    override_reason: Optional[str] = None
    overridden_at: Optional[datetime] = None


# ── API request / response models ────────────────────────────────────────────

class OverrideRequest(BaseModel):
    decision: DocumentStatus
    reason: str
    officer_name: str


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
