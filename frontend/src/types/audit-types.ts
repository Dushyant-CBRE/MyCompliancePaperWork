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
