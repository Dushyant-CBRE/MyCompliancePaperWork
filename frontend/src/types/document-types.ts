export type DocStatus = 'Approved' | 'Rejected' | 'Needs Review';

export interface Document {
    id: string;
    site: string;
    vendor: string;
    ppmType: string;
    documentDate: string;
    uploadDate: string;
    status: DocStatus;
    confidence: number;
    flags: string[];
    remedial: boolean;
}

export interface UploadMetadata {
    expected_site_name?: string;
    expected_ppm_type?: string;
    expected_document_date?: string;
    expected_document_type?: string;
    expected_vendor_name?: string;
    notes?: string;
}

export interface UploadResponse {
    document_id: string;
    filename: string;
    message: string;
}

export interface AnalyticsSummary {
    total_documents: number;
    auto_approved: number;
    manual_review: number;
    requires_attention: number;
    approved: number;
    rejected: number;
    avg_confidence: number;
    remedial_pass: number;
    remedial_minor: number;
    remedial_critical: number;
    auto_approval_rate: number;
    avg_processing_time_seconds: number;
    processing_buckets: { time: string; count: number }[];
    confidence_distribution: { range: string; count: number }[];
    site_breakdown: { site: string; approved: number; review: number; remedial: number }[];
    ppm_distribution: { type: string; count: number }[];
}

// ── Backend types for Dashboard integration ──────────────────────────────────

export type BackendDocStatus =
    | 'pending'
    | 'processing'
    | 'auto_approved'
    | 'manual_review'
    | 'requires_attention'
    | 'approved'
    | 'rejected';

export type RemedialClassification = 'PASS' | 'REMEDIAL_MINOR' | 'REMEDIAL_CRITICAL' | 'UNKNOWN';

export interface BackendDocumentMetadata {
    expected_site_name: string | null;
    expected_ppm_type: string | null;
    expected_document_date: string | null;
    expected_document_type: string | null;
    expected_vendor_name: string | null;
    notes: string | null;
}

export interface BackendExtractedFields {
    site_name: string | null;
    site_name_confidence: number;
    site_name_source: string | null;
    ppm_reference: string | null;
    ppm_reference_confidence: number;
    ppm_reference_source: string | null;
    inspection_date: string | null;
    inspection_date_confidence: number;
    inspection_date_source: string | null;
    inspector_name: string | null;
    inspector_name_confidence: number;
    inspector_name_source: string | null;
    equipment_id: string | null;
    equipment_id_confidence: number;
    equipment_id_source: string | null;
    document_type: string | null;
    document_type_confidence: number;
    document_type_source: string | null;
    vendor_name: string | null;
    vendor_name_confidence: number;
    vendor_name_source: string | null;
    certificate_number: string | null;
    certificate_number_confidence: number;
    certificate_number_source: string | null;
    next_service_date: string | null;
    next_service_date_confidence: number;
    next_service_date_source: string | null;
    overall_outcome: string | null;
    overall_outcome_confidence: number;
    overall_outcome_source: string | null;
    page_count: number | null;
    client_name: string | null;
    client_name_confidence: number;
    client_name_source: string | null;
    key_readings: { name: string; value: string; unit: string; status: string }[];
    overall_extraction_confidence: number;
    raw_text_length: number;
}

export interface BackendValidationResult {
    site_name_match: number;
    ppm_reference_match: number;
    date_valid: boolean;
    date_validity_score: number;
    inspector_valid: boolean;
    inspector_validity_score: number;
    issues: string[];
    overall_validation_confidence: number;
    checks: { check: string; status: 'pass' | 'fail'; detail: string }[];
}

export interface BackendRemedialResult {
    classification: RemedialClassification;
    classification_confidence: number;
    findings: string[];
    critical_items: string[];
    minor_items: string[];
    reasoning: string;
    evidence: { text: string; page: number; severity: 'High' | 'Medium' | 'Low' }[];
}

export interface BackendConfidenceScore {
    extraction_score: number;
    validation_score: number;
    remedial_score: number;
    overall_score: number;
    decision: BackendDocStatus;
}

export interface BackendDocumentInsights {
    compliance_status: string;
    risk_level: string;
    days_until_next_service: number | null;
    is_overdue: boolean;
    fields_extracted: number;
    fields_total: number;
    completeness_pct: number;
    flags: string[];
    sla_remaining: string | null;
    score_breakdown: { label: string; score: number; weight: number }[];
}

export interface BackendAgentState {
    iterations: number;
    steps: {
        iteration: number;
        tool_name: string;
        tool_args: Record<string, unknown>;
        result_summary: string;
    }[];
    tools_called: string[];
    final_rationale: string;
    orchestrator_routing: string | null;
}

export interface DocumentRecord {
    document_id: string;
    filename: string;
    blob_url: string | null;
    status: BackendDocStatus;
    uploaded_at: string;
    processed_at: string | null;
    metadata: BackendDocumentMetadata | null;
    extracted_fields: BackendExtractedFields | null;
    validation_result: BackendValidationResult | null;
    remedial_result: BackendRemedialResult | null;
    confidence_score: BackendConfidenceScore | null;
    agent_state: BackendAgentState | null;
    insights: BackendDocumentInsights | null;
    override_by: string | null;
    override_reason: string | null;
    overridden_at: string | null;
}

export interface DocumentListResponse {
    documents: DocumentRecord[];
    total: number;
}

export interface OverrideRequest {
    decision: 'approved' | 'rejected';
    reason: string;
    officer_name: string;
}

export interface DashboardStats {
    totalDocuments: number;
    approved: number;
    needsReview: number;
    rejected: number;
}