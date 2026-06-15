import { AlertTriangle } from 'lucide-react';
import type { RemedialEvidence, ValidationCheck } from '../../types/review-types';

interface RemedialDetectionTabProps {
    evidence: RemedialEvidence[];
    validationChecks?: ValidationCheck[];
}

export function RemedialDetectionTab({ evidence, validationChecks }: RemedialDetectionTabProps) {
    const hasEvidence = evidence && evidence.length > 0;
    const hasHigh = hasEvidence && evidence.some((e) => e.severity === 'High');

    return (
        <div>
            {!hasEvidence ? (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                    <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-green-900">No Remedial Actions Detected</h3>
                    </div>
                    <p className="text-sm text-green-800">No remedial evidence was found in this document.</p>
                </div>
            ) : hasHigh ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                    <div className="flex items-center gap-3 mb-2">
                        <AlertTriangle className="w-5 h-5 text-red-700" />
                        <h3 className="text-red-900">Remedial Actions Detected</h3>
                    </div>
                    <p className="text-sm text-red-800">
                        Critical actions require immediate attention. Review evidence below.
                    </p>
                </div>
            ) : (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                    <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-yellow-800">Advisory Items Detected</h3>
                    </div>
                    <p className="text-sm text-yellow-800">These are advisory findings; review and confirm as needed.</p>
                </div>
            )}

            <div className="space-y-3">
                {evidence.map((item, idx) => (
                    <div
                        key={idx}
                        className={`p-4 rounded-lg border ${
                            item.severity === 'High'
                                ? 'bg-red-50 border-red-200'
                                : 'bg-yellow-50 border-yellow-200'
                        }`}
                    >
                        <div className="flex items-start justify-between mb-2">
                            <span
                                className={`text-xs px-2 py-1 rounded ${
                                    item.severity === 'High'
                                        ? 'bg-red-100 text-red-800'
                                        : 'bg-yellow-100 text-yellow-800'
                                }`}
                            >
                                {item.severity} Severity
                            </span>
                            <span className="text-sm text-muted-foreground">Page {item.page}</span>
                        </div>
                        <p
                            className={`text-sm ${
                                item.severity === 'High' ? 'text-red-800' : 'text-yellow-800'
                            }`}
                        >
                            {item.text}
                        </p>
                        <button className="text-sm text-primary hover:underline mt-2">
                            Jump to highlight
                        </button>
                    </div>
                ))}
            </div>
            {/* Low-visibility Validation Notes: collapsed by default */}
            {validationChecks && validationChecks.length > 0 && (
                <details className="mt-6 text-sm text-muted-foreground">
                    <summary className="cursor-pointer">Validation Notes ({validationChecks.length})</summary>
                    <div className="mt-2 space-y-2">
                        {validationChecks.map((c, i) => (
                            <div key={i} className="p-2 rounded border border-border bg-background">
                                <div className="text-xs font-medium">{c.check}</div>
                                {c.detail && <div className="text-xs text-muted-foreground">{c.detail}</div>}
                                <div className="text-xs text-muted-foreground">Status: {c.status}</div>
                            </div>
                        ))}
                    </div>
                </details>
            )}
        </div>
    );
}
