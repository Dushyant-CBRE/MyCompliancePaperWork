import type { UploadMetadata, UploadResponse } from "../types/document-types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export async function uploadDocument(
    file: File,
    metadata: UploadMetadata = {},
): Promise<UploadResponse> {
    const form = new FormData();
    form.append('file', file);

    if (metadata.expected_site_name) form.append('expected_site_name', metadata.expected_site_name);
    if (metadata.expected_ppm_type) form.append('expected_ppm_type', metadata.expected_ppm_type);
    if (metadata.expected_document_date) form.append('expected_document_date', metadata.expected_document_date);
    if (metadata.expected_document_type) form.append('expected_document_type', metadata.expected_document_type);
    if (metadata.expected_vendor_name) form.append('expected_vendor_name', metadata.expected_vendor_name);
    if (metadata.notes) form.append('notes', metadata.notes);

    const res = await fetch(`${API_BASE}/api/upload`, {
        method: 'POST',
        body: form,
    });

    if (!res.ok) {
        const body = await res.json().catch(() => ({})) as { detail?: string };
        throw new Error(body.detail ?? `Upload failed (${res.status})`);
    }

    return res.json() as Promise<UploadResponse>;
}
