interface ThresholdsCardProps {
    autoApprove: number;
    manualReview: number;
    onAutoApproveChange: (value: number) => void;
    onManualReviewChange: (value: number) => void;
}

export function ThresholdsCard({
    autoApprove,
    manualReview,
    onAutoApproveChange,
    onManualReviewChange,
}: ThresholdsCardProps) {
    return (
        <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="mb-4">Confidence Thresholds</h3>
            <div className="space-y-4">
                <div>
                    <label className="block mb-2 text-sm font-medium">
                        Auto-Approve Threshold
                    </label>
                    <div className="flex items-center gap-4">
                        <input
                            type="range"
                            min="0"
                            max="100"
                            value={autoApprove}
                            onChange={(e) => onAutoApproveChange(Number(e.target.value))}
                            className="flex-1 accent-primary"
                        />
                        <input
                            type="number"
                            min="0"
                            max="100"
                            value={autoApprove}
                            onChange={(e) => onAutoApproveChange(Number(e.target.value))}
                            className="w-20 px-3 py-2 bg-input-background rounded-lg border-0 focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                        />
                        <span className="text-sm">%</span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-2">
                        Documents with confidence above this threshold will be auto-approved
                    </p>
                </div>

                <div>
                    <label className="block mb-2 text-sm font-medium">
                        Manual Review Threshold
                    </label>
                    <div className="flex items-center gap-4">
                        <input
                            type="range"
                            min="0"
                            max="100"
                            value={manualReview}
                            onChange={(e) => onManualReviewChange(Number(e.target.value))}
                            className="flex-1 accent-primary"
                        />
                        <input
                            type="number"
                            min="0"
                            max="100"
                            value={manualReview}
                            onChange={(e) => onManualReviewChange(Number(e.target.value))}
                            className="w-20 px-3 py-2 bg-input-background rounded-lg border-0 focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                        />
                        <span className="text-sm">%</span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-2">
                        Documents below this threshold require manual review
                    </p>
                </div>
            </div>
        </div>
    );
}
