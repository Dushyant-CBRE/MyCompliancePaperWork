export type DocStatus = 'Auto-Approved' | 'Needs Review' | 'Remedial Detected';

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