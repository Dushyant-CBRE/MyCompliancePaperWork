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
