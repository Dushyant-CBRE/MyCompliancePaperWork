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