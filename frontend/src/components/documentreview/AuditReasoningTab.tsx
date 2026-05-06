import type { AuditData } from '../../types/review-types';

interface AuditReasoningTabProps {
    data?: AuditData;
}

export function AuditReasoningTab({ data }: AuditReasoningTabProps) {
    if (!data) return null;
    return (
        <div className="space-y-4">
            <h3 className="mb-4">AI Decision Reasoning</h3>
            <div className="bg-muted/30 rounded-lg p-4 space-y-3">
                <div>
                    <span className="text-sm text-muted-foreground">Model Decision</span>
                    <p className="mt-1">{data.modelDecision}</p>
                </div>
                <div>
                    <span className="text-sm text-muted-foreground">Processing Time</span>
                    <p className="mt-1">{data.processingTime}</p>
                </div>
                <div>
                    <span className="text-sm text-muted-foreground">Timestamp</span>
                    <p className="mt-1">{data.timestamp}</p>
                </div>
                <div>
                    <span className="text-sm text-muted-foreground">Confidence Breakdown</span>
                    <div className="mt-2 space-y-2">
                        <div className="flex justify-between text-sm">
                            <span>Field Extraction</span>
                            <span>{data.extractionScore}%</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span>Validation</span>
                            <span>{data.validationScore}%</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span>Remedial Detection</span>
                            <span>{data.remedialScore}%</span>
                        </div>
                    </div>
                </div>
                {data.iterations !== undefined && (
                    <div>
                        <span className="text-sm text-muted-foreground">Agent Iterations</span>
                        <p className="mt-1">{data.iterations}</p>
                    </div>
                )}
                {data.toolsCalled && data.toolsCalled.length > 0 && (
                    <div>
                        <span className="text-sm text-muted-foreground">Tools Used</span>
                        <p className="mt-1 text-sm">{data.toolsCalled.join(', ')}</p>
                    </div>
                )}
            </div>
        </div>
    );
}
