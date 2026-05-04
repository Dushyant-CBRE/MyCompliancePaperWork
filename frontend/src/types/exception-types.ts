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
