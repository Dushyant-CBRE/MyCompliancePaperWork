import { AlertTriangle } from 'lucide-react';
import type { RemedialEvidence } from '../../types/review-types';

interface RemedialDetectionTabProps {
    evidence: RemedialEvidence[];
}

export function RemedialDetectionTab({ evidence }: RemedialDetectionTabProps) {
    return (
        <div>
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                <div className="flex items-center gap-3 mb-2">
                    <AlertTriangle className="w-5 h-5 text-red-700" />
                    <h3 className="text-red-900">Remedial Actions Detected</h3>
                </div>
                <p className="text-sm text-red-800">
                    Critical actions require immediate attention. Review evidence below.
                </p>
            </div>

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
        </div>
    );
}
