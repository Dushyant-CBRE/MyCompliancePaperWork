import type { AuditEntry } from '../types/audit-types';
import { PageHeader } from '../components/PageHeader';
import { AuditToolbar } from '../components/auditlog/AuditToolbar';
import { AuditTable } from '../components/auditlog/AuditTable';

const mockAuditEntries: AuditEntry[] = [
    {
        id: '1',
        timestamp: '2026-04-22 14:32:18',
        user: 'Priya Sharma',
        action: 'Rejected',
        document: 'Fire_Safety_PPM_DLF_2026-04-15.pdf',
        details: "Changed status to 'Rejected'",
        reason: 'Remedial misclassified',
        trainingFeedback: true,
    },
    {
        id: '2',
        timestamp: '2026-04-22 13:15:42',
        user: 'System (AI)',
        action: 'Approved',
        document: 'Electrical_PPM_Udyog_Vihar_2026-04-18.pdf',
        details: 'Confidence: 92%, All validation checks passed',
        reason: null,
        trainingFeedback: false,
    },
    {
        id: '3',
        timestamp: '2026-04-22 12:48:09',
        user: 'Rajesh Kumar',
        action: 'Reject',
        document: 'HVAC_PPM_Golf_Course_2026-04-10.pdf',
        details: 'Document rejected due to missing required fields',
        reason: 'Missing signatures',
        trainingFeedback: false,
    },
    {
        id: '4',
        timestamp: '2026-04-22 11:23:55',
        user: 'System (AI)',
        action: 'Needs Review',
        document: 'Fire_Safety_PPM_DLF_2026-04-12.pdf',
        details: "Keywords found: 'immediate action required'",
        reason: null,
        trainingFeedback: false,
    },
    {
        id: '5',
        timestamp: '2026-04-22 10:05:31',
        user: 'Priya Sharma',
        action: 'Batch Approve',
        document: 'Multiple documents (8)',
        details: 'Batch approved 8 documents with confidence ≥85%',
        reason: null,
        trainingFeedback: false,
    },
];

export function AuditLog() {
    return (
        <div className="p-6">
            <PageHeader
                title="Audit Log"
                subtitle="Complete decision history and action tracking"
            />
            <div className="bg-card border border-border rounded-lg">
                <AuditToolbar />
                <AuditTable entries={mockAuditEntries} />
                <div className="p-4 border-t border-border flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">Showing 5 of 1,247 entries</p>
                    <div className="flex items-center gap-2">
                        <button className="px-3 py-1 bg-muted rounded hover:bg-muted/80 transition-colors text-sm">
                            Previous
                        </button>
                        <button className="px-3 py-1 bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors text-sm">
                            Next
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
