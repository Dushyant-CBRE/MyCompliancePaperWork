import type { DocumentRecord, OverrideRequest } from '../types/document-types';
import type {
    ReviewDocument,
    ExtractedField,
    ValidationCheck,
    RemedialEvidence,
    AuditData,
} from '../types/review-types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

// ── API functions ────────────────────────────────────────────────────────────

export async function getDocumentById(id: string): Promise<DocumentRecord> {
    const res = await fetch(`${BASE_URL}/api/documents/${id}`);
    if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Failed to fetch document (${res.status})`);
    }
    return res.json() as Promise<DocumentRecord>;
}

export async function overrideDocument(id: string, body: OverrideRequest): Promise<DocumentRecord> {
    const res = await fetch(`${BASE_URL}/api/documents/${id}/override`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Override failed (${res.status})`);
    }
    return res.json() as Promise<DocumentRecord>;
}

export function getDocumentPdfUrl(id: string): string {
    return `${BASE_URL}/api/documents/${id}/pdf`;
}

// ── Mapping helpers ──────────────────────────────────────────────────────────

function deriveAiDecision(record: DocumentRecord): string {
    const classification = record.remedial_result?.classification;
    if (classification === 'REMEDIAL_CRITICAL') return 'Remedial Critical';
    if (classification === 'REMEDIAL_MINOR') return 'Remedial Minor';
    if (record.status === 'auto_approved' || record.status === 'approved') return 'AI Approved';
    if (record.status === 'rejected') return 'Rejected';
    if (record.status === 'manual_review' || record.status === 'requires_attention') return 'Needs Review';
    return 'Processing';
}

function deriveRiskLevel(record: DocumentRecord): string {
    if (record.insights?.risk_level) return record.insights.risk_level;
    const classification = record.remedial_result?.classification;
    if (classification === 'REMEDIAL_CRITICAL') return 'Critical';
    if (classification === 'REMEDIAL_MINOR') return 'Medium';
    if ((record.confidence_score?.overall_score ?? 100) < 50) return 'High';
    return 'Low';
}

function mapExtractedFields(record: DocumentRecord): ExtractedField[] {
    const ef = record.extracted_fields;
    if (!ef) return [];

    const fieldDefs: { label: string; value: string | null; confidence: number; source: string | null }[] = [
        { label: 'Site Name', value: ef.site_name, confidence: ef.site_name_confidence, source: ef.site_name_source },
        { label: 'PPM Reference', value: ef.ppm_reference, confidence: ef.ppm_reference_confidence, source: ef.ppm_reference_source },
        { label: 'Inspection Date', value: ef.inspection_date, confidence: ef.inspection_date_confidence, source: ef.inspection_date_source },
        { label: 'Inspector Name', value: ef.inspector_name, confidence: ef.inspector_name_confidence, source: ef.inspector_name_source },
        { label: 'Equipment ID', value: ef.equipment_id, confidence: ef.equipment_id_confidence, source: ef.equipment_id_source },
        { label: 'Document Type', value: ef.document_type, confidence: ef.document_type_confidence, source: ef.document_type_source },
        { label: 'Vendor Name', value: ef.vendor_name, confidence: ef.vendor_name_confidence, source: ef.vendor_name_source },
        { label: 'Certificate Number', value: ef.certificate_number, confidence: ef.certificate_number_confidence, source: ef.certificate_number_source },
        { label: 'Next Service Date', value: ef.next_service_date, confidence: ef.next_service_date_confidence, source: ef.next_service_date_source },
        { label: 'Overall Outcome', value: ef.overall_outcome, confidence: ef.overall_outcome_confidence, source: ef.overall_outcome_source },
    ];

    return fieldDefs.map((f) => ({
        label: f.label,
        value: f.value ?? 'N/A',
        confidence: Math.min(100, Math.round(f.confidence > 1 ? f.confidence : f.confidence * 100)),
        source: f.source ?? '\u2014',
    }));
}

function mapValidationChecks(record: DocumentRecord): ValidationCheck[] {
    const vr = record.validation_result;
    if (!vr) return [];

    // Use pre-structured checks if available
    if (vr.checks && vr.checks.length > 0) {
        return vr.checks.map((c) => ({
            check: c.check,
            status: c.status as 'pass' | 'fail',
            detail: c.detail || undefined,
        }));
    }

    // Fallback: derive from scalar fields
    const checks: ValidationCheck[] = [
        {
            check: 'Site name matches expected',
            status: vr.site_name_match >= 80 ? 'pass' : 'fail',
            detail: vr.site_name_match < 80 ? `Match score: ${vr.site_name_match}%` : undefined,
        },
        {
            check: 'PPM reference matches expected',
            status: vr.ppm_reference_match >= 80 ? 'pass' : 'fail',
            detail: vr.ppm_reference_match < 80 ? `Match score: ${vr.ppm_reference_match}%` : undefined,
        },
        {
            check: 'Document date is valid',
            status: vr.date_valid ? 'pass' : 'fail',
            detail: !vr.date_valid ? `Validity score: ${vr.date_validity_score}%` : undefined,
        },
        {
            check: 'Inspector is valid',
            status: vr.inspector_valid ? 'pass' : 'fail',
            detail: !vr.inspector_valid ? `Validity score: ${vr.inspector_validity_score}%` : undefined,
        },
    ];

    // Add each issue as a fail row
    for (const issue of vr.issues) {
        checks.push({ check: issue, status: 'fail' });
    }

    return checks;
}

function mapRemedialEvidence(record: DocumentRecord): RemedialEvidence[] {
    const rr = record.remedial_result;
    if (!rr) return [];

    // Use structured evidence if available
    if (rr.evidence && rr.evidence.length > 0) {
        return rr.evidence.map((e) => ({
            text: e.text,
            page: e.page,
            severity: e.severity,
        }));
    }

    // Fallback: derive from critical/minor items
    const evidence: RemedialEvidence[] = [];
    for (const item of rr.critical_items) {
        evidence.push({ text: item, page: 1, severity: 'High' });
    }
    for (const item of rr.minor_items) {
        evidence.push({ text: item, page: 1, severity: 'Medium' });
    }
    return evidence;
}

function formatProcessingTime(uploadedAt: string, processedAt: string | null): string {
    if (!processedAt) return '\u2014';
    const diffMs = new Date(processedAt).getTime() - new Date(uploadedAt).getTime();
    if (diffMs < 0) return '\u2014';
    const totalSeconds = Math.round(diffMs / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    if (minutes === 0) return `${seconds}s`;
    return `${minutes}m ${seconds}s`;
}

function mapAuditData(record: DocumentRecord): AuditData {
    const cs = record.confidence_score;
    const reasoning =
        record.agent_state?.final_rationale ||
        record.remedial_result?.reasoning ||
        'No reasoning available';

    return {
        modelDecision: reasoning,
        processingTime: formatProcessingTime(record.uploaded_at, record.processed_at),
        timestamp: record.processed_at
            ? new Date(record.processed_at).toLocaleString()
            : '\u2014',
        extractionScore: cs?.extraction_score ?? 0,
        validationScore: cs?.validation_score ?? 0,
        remedialScore: cs?.remedial_score ?? 0,
        iterations: record.agent_state?.iterations,
        toolsCalled: record.agent_state?.tools_called,
    };
}

// ── Main mapping function ────────────────────────────────────────────────────

export function mapDocumentToReview(record: DocumentRecord): {
    doc: ReviewDocument;
    fields: ExtractedField[];
    checks: ValidationCheck[];
    evidence: RemedialEvidence[];
    auditData: AuditData;
    pdfUrl: string;
} {
    const ef = record.extracted_fields;
    const meta = record.metadata;

    const doc: ReviewDocument = {
        name: record.filename,
        site: ef?.site_name || meta?.expected_site_name || 'Unknown',
        ppmType: ef?.document_type || meta?.expected_ppm_type || 'Unknown',
        confidence: Math.round(record.confidence_score?.overall_score ?? 0),
        aiDecision: deriveAiDecision(record),
        riskLevel: deriveRiskLevel(record),
        slaRemaining: record.insights?.sla_remaining ?? '\u2014',
    };

    return {
        doc,
        fields: mapExtractedFields(record),
        checks: mapValidationChecks(record),
        evidence: mapRemedialEvidence(record),
        auditData: mapAuditData(record),
        pdfUrl: getDocumentPdfUrl(record.document_id),
    };
}
