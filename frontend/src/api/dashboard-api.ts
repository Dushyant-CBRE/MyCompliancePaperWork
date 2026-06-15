import type {
    DocumentListResponse,
    DocumentRecord,
    OverrideRequest,
    Document,
    DocStatus,
} from '../types/document-types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export async function getDocuments(status?: string, limit = 50): Promise<DocumentListResponse> {
    const params = new URLSearchParams({ limit: String(limit) });
    if (status) params.append('status', status);

    const res = await fetch(`${API_BASE}/api/documents?${params}`);
    if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Failed to fetch documents (${res.status})`);
    }
    return res.json() as Promise<DocumentListResponse>;
}

export async function overrideDocument(id: string, body: OverrideRequest): Promise<DocumentRecord> {
    const res = await fetch(`${API_BASE}/api/documents/${id}/override`, {
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

export function mapDocumentRecord(record: DocumentRecord): Document {
    const ef = record.extracted_fields;
    const meta = record.metadata;
    const rem = record.remedial_result;

    // Status mapping
    let status: DocStatus = 'Needs Review';
    if (record.status === 'auto_approved' || record.status === 'approved') {
        status = 'Approved';
    } else if (record.status === 'rejected') {
        status = 'Rejected';
    }

    // Flags: prefer pre-computed insights, fallback to manual derivation
    let flags: string[] = [];
    if (record.insights?.flags && record.insights.flags.length > 0) {
        flags = record.insights.flags;
    } else {
        // If no pre-computed insights flags, derive only from remedial findings
        // and completeness/operational signals. Do NOT surface raw validation
        // issues here to avoid cluttering the dashboard with metadata checks.
        if (rem?.classification === 'REMEDIAL_CRITICAL') flags.push('Remedial Critical');
        else if (rem?.classification === 'REMEDIAL_MINOR') flags.push('Remedial Minor');
        if (record.extracted_fields && record.extracted_fields.overall_extraction_confidence && record.extracted_fields.overall_extraction_confidence < 70) {
            flags.push('Low extraction confidence');
        }
    }

    return {
        id: record.document_id,
        site: ef?.site_name || meta?.expected_site_name || record.filename,
        vendor: ef?.vendor_name || meta?.expected_vendor_name || '\u2014',
        ppmType: ef?.ppm_reference || meta?.expected_ppm_type || '\u2014',
        documentDate: ef?.inspection_date || meta?.expected_document_date || '\u2014',
        uploadDate: record.uploaded_at?.slice(0, 10) || '\u2014',
        status,
        confidence: Math.round(record.confidence_score?.overall_score ?? 0),
        flags,
        // Use backend insights.compliance_status as the authoritative source
        remedial: (record.insights?.compliance_status === 'Remedial Action Required') || (record.insights?.compliance_status === 'Non-Compliant'),
        complianceStatus: record.insights?.compliance_status ?? null,
        riskLevel: record.insights?.risk_level ?? null,
    };
}
