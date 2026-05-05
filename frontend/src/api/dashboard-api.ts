import type {
    DocumentListResponse,
    DocumentRecord,
    OverrideRequest,
    Document,
    DocStatus,
} from '../types/document-types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function getDocuments(status?: string, limit = 50): Promise<DocumentListResponse> {
    const params = new URLSearchParams({ limit: String(limit) });
    if (status) params.append('status', status);

    const res = await fetch(`${BASE_URL}/api/documents?${params}`);
    if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Failed to fetch documents (${res.status})`);
    }
    return res.json() as Promise<DocumentListResponse>;
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

export function mapDocumentRecord(record: DocumentRecord): Document {
    const ef = record.extracted_fields;
    const meta = record.metadata;
    const rem = record.remedial_result;

    // Status mapping
    let status: DocStatus = 'Needs Review';
    if (
        rem?.classification === 'REMEDIAL_MINOR' ||
        rem?.classification === 'REMEDIAL_CRITICAL'
    ) {
        status = 'Remedial Detected';
    } else if (record.status === 'auto_approved' || record.status === 'approved') {
        status = 'Auto-Approved';
    }

    // Flags: prefer pre-computed insights, fallback to manual derivation
    let flags: string[] = [];
    if (record.insights?.flags && record.insights.flags.length > 0) {
        flags = record.insights.flags;
    } else {
        if (record.validation_result?.issues) {
            flags = [...record.validation_result.issues];
        }
        if (rem?.classification === 'REMEDIAL_CRITICAL') flags.push('Remedial Critical');
        else if (rem?.classification === 'REMEDIAL_MINOR') flags.push('Remedial Minor');
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
        remedial:
            rem?.classification === 'REMEDIAL_MINOR' ||
            rem?.classification === 'REMEDIAL_CRITICAL',
    };
}
