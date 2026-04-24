export function AuditReasoningTab() {
    return (
        <div className="space-y-4">
            <h3 className="mb-4">AI Decision Reasoning</h3>
            <div className="bg-muted/30 rounded-lg p-4 space-y-3">
                <div>
                    <span className="text-sm text-muted-foreground">Model Decision</span>
                    <p className="mt-1">
                        Document flagged for remedial actions requiring immediate attention
                    </p>
                </div>
                <div>
                    <span className="text-sm text-muted-foreground">Processing Time</span>
                    <p className="mt-1">1m 34s</p>
                </div>
                <div>
                    <span className="text-sm text-muted-foreground">Timestamp</span>
                    <p className="mt-1">2026-04-20 14:32:18 UTC</p>
                </div>
                <div>
                    <span className="text-sm text-muted-foreground">Confidence Breakdown</span>
                    <div className="mt-2 space-y-2">
                        <div className="flex justify-between text-sm">
                            <span>OCR Quality</span>
                            <span>94%</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span>Field Extraction</span>
                            <span>91%</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span>Remedial Detection</span>
                            <span>87%</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
