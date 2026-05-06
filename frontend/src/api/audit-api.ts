import type { AuditEntry } from '../types/audit-types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

interface BackendAuditEntry {
    entry_id: string;
    timestamp: string;
    user: string;
    status: string;
    document: string;
    document_id: string;
    details: string;
}

interface BackendAuditResponse {
    entries: BackendAuditEntry[];
    total: number;
}

function mapStatus(status: string): string {
    switch (status) {
        case 'auto_approved':
        case 'approved':
            return 'Approved';
        case 'rejected':
            return 'Rejected';
        default:
            return 'Needs Review';
    }
}

function formatTimestamp(iso: string): string {
    const d = new Date(iso);
    const pad = (n: number) => n.toString().padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function mapEntry(entry: BackendAuditEntry): AuditEntry {
    return {
        id: entry.entry_id,
        timestamp: formatTimestamp(entry.timestamp),
        user: entry.user,
        action: mapStatus(entry.status),
        document: entry.document,
        documentId: entry.document_id,
        details: entry.details,
        reason: null,
        trainingFeedback: false,
    };
}

export interface AuditLogResult {
    entries: AuditEntry[];
    total: number;
}

export async function fetchAuditLog(params?: {
    limit?: number;
    documentId?: string;
}): Promise<AuditLogResult> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.documentId) searchParams.set('document_id', params.documentId);

    const query = searchParams.toString();
    const url = `${API_BASE}/api/audit${query ? `?${query}` : ''}`;

    const res = await fetch(url);
    if (!res.ok) {
        throw new Error(`Failed to fetch audit log: ${res.status}`);
    }

    const data: BackendAuditResponse = await res.json();
    return {
        entries: data.entries.map(mapEntry),
        total: data.total,
    };
}
