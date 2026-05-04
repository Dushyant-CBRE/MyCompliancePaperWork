import type { ExtractedField, ValidationCheck, RemedialEvidence } from '../../types/review-types';
import { ExtractedFieldsTab } from './ExtractedFieldsTab';
import { ValidationChecksTab } from './ValidationChecksTab';
import { RemedialDetectionTab } from './RemedialDetectionTab';
import { AuditReasoningTab } from './AuditReasoningTab';

type TabId = 'fields' | 'validation' | 'remedial' | 'audit';

interface AnalysisPanelProps {
    activeTab: TabId;
    onTabChange: (tab: TabId) => void;
    fields: ExtractedField[];
    checks: ValidationCheck[];
    evidence: RemedialEvidence[];
}

const tabs: { id: TabId; label: string }[] = [
    { id: 'fields', label: 'Extracted Fields' },
    { id: 'validation', label: 'Validation Checks' },
    { id: 'remedial', label: 'Remedial Detection' },
    { id: 'audit', label: 'Audit & Reasoning' },
];

export function AnalysisPanel({
    activeTab,
    onTabChange,
    fields,
    checks,
    evidence,
}: AnalysisPanelProps) {
    return (
        <div className="w-[480px] bg-card border-l border-border flex flex-col">
            <div className="border-b border-border">
                <div className="flex">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => onTabChange(tab.id)}
                            className={`flex-1 px-4 py-3 text-sm transition-colors border-b-2 ${
                                activeTab === tab.id
                                    ? 'border-primary text-primary'
                                    : 'border-transparent text-muted-foreground hover:text-foreground'
                            }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>
            </div>

            <div className="flex-1 overflow-auto p-6">
                {activeTab === 'fields' && <ExtractedFieldsTab fields={fields} />}
                {activeTab === 'validation' && <ValidationChecksTab checks={checks} />}
                {activeTab === 'remedial' && <RemedialDetectionTab evidence={evidence} />}
                {activeTab === 'audit' && <AuditReasoningTab />}
            </div>
        </div>
    );
}
