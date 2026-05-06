import type { ReviewRequest, ReviewResponse } from '../types/review-types';
import type {
    ExtractedField,
    ValidationCheck,
    RemedialEvidence,
    ReviewDocument,
} from '../types/review-types';
import type { DocumentRecord } from '../types/document-types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL as string;

export interface ReviewDocumentDetail {
    doc: ReviewDocument;
    fields: ExtractedField[];
    checks: ValidationCheck[];
    evidence: RemedialEvidence[];
    blobUrl: string | null;
}

export async function getDocumentForReview(id: string): Promise<ReviewDocumentDetail> {
    const res = await fetch(`${BASE_URL}/api/documents/${id}`);
    if (!res.ok) {
        const data = await res.json().catch(() => ({})) as { detail?: string };
        throw new Error(data.detail ?? `Failed to fetch document (${res.status})`);
    }
    const record = await res.json() as DocumentRecord;
    return mapDocumentRecord(record);
}

function mapDocumentRecord(record: DocumentRecord): ReviewDocumentDetail {
    const ef = record.extracted_fields;
    const meta = record.metadata;
    const rem = record.remedial_result;
    const insights = record.insights;

    const statusLabelMap: Record<string, string> = {
        pending: 'Pending',
        processing: 'Processing',
        auto_approved: 'Auto-Approved',
        manual_review: 'Needs Review',
        requires_attention: 'Requires Attention',
        approved: 'Approved',
        rejected: 'Rejected',
    };

    const doc: ReviewDocument = {
        name: record.filename,
        site: ef?.site_name || meta?.expected_site_name || '—',
        ppmType: ef?.ppm_reference || meta?.expected_ppm_type || '—',
        confidence: Math.round(record.confidence_score?.overall_score ?? 0),
        status: statusLabelMap[record.status] ?? record.status,
        aiDecision: insights?.compliance_status || record.status,
        riskLevel: insights?.risk_level || '—',
        slaRemaining: insights?.sla_remaining || '—',
    };

    const fields: ExtractedField[] = ef
        ? [
              { label: 'Site Name', value: ef.site_name ?? '—', confidence: Math.round(ef.site_name_confidence), source: 'Extracted' },
              { label: 'PPM Type', value: ef.ppm_reference ?? '—', confidence: Math.round(ef.ppm_reference_confidence), source: 'Extracted' },
              { label: 'Document Date', value: ef.inspection_date ?? '—', confidence: Math.round(ef.inspection_date_confidence), source: 'Extracted' },
              { label: 'Vendor Name', value: ef.vendor_name ?? '—', confidence: Math.round(ef.vendor_name_confidence), source: 'Extracted' },
              { label: 'Inspector Name', value: ef.inspector_name ?? '—', confidence: Math.round(ef.inspector_name_confidence), source: 'Extracted' },
              { label: 'Certificate Number', value: ef.certificate_number ?? '—', confidence: Math.round(ef.certificate_number_confidence), source: 'Extracted' },
          ]
        : [];

    const checks: ValidationCheck[] = record.validation_result?.checks?.map((c) => ({
        check: c.check,
        status: c.status,
        detail: c.detail || undefined,
    })) ?? [];

    const evidence: RemedialEvidence[] = rem?.evidence?.map((e) => ({
        text: e.text,
        page: e.page,
        severity: e.severity,
    })) ?? [];

    return { doc, fields, checks, evidence, blobUrl: record.blob_url ?? null };
}

/**
 * Fetches the PDF bytes via the backend proxy (which authenticates with Azure),
 * and returns a local object URL safe to use in an <iframe> or <a download>.
 * The caller is responsible for calling URL.revokeObjectURL() when done.
 */
export async function getPdfObjectUrl(documentId: string): Promise<string> {
    const res = await fetch(`${BASE_URL}/api/documents/${documentId}/file`);
    if (!res.ok) {
        const data = await res.json().catch(() => ({})) as { detail?: string };
        throw new Error(data.detail ?? `Failed to fetch PDF (${res.status})`);
    }
    const blob = await res.blob();
    return URL.createObjectURL(blob);
}

export async function submitReview(
    documentId: string,
    body: ReviewRequest,
): Promise<ReviewResponse> {
    const res = await fetch(`${BASE_URL}/api/documents/${documentId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const data = await res.json().catch(() => ({})) as { detail?: string };
        throw new Error(data.detail ?? `Review submission failed (${res.status})`);
    }

    return res.json() as Promise<ReviewResponse>;
}
