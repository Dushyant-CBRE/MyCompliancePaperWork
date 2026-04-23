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

export type Severity = 'Critical' | 'High' | 'Medium' | 'Low';

export interface Exception {
    id: string;
    site: string;
    vendor: string;
    ppmType: string;
    severity: Severity;
    reason: string;
    confidence: number;
    sla: string;
    assignee: string | null;
}

export interface AuditEntry {
    id: string;
    timestamp: string;
    user: string;
    action: string;
    document: string;
    details: string;
    reason: string | null;
    trainingFeedback: boolean;
}

export interface ExtractedField {
    label: string;
    value: string;
    confidence: number;
    source: string;
}

export interface ValidationCheck {
    check: string;
    status: 'pass' | 'fail';
    detail?: string;
}

export interface RemedialEvidence {
    text: string;
    page: number;
    severity: 'High' | 'Medium' | 'Low';
}

export interface ReviewDocument {
    name: string;
    site: string;
    ppmType: string;
    confidence: number;
    aiDecision: string;
    riskLevel: string;
    slaRemaining: string;
}
