interface QualitySafetyCardProps {
    needsReviewCount: number;
}

export function QualitySafetyCard({ needsReviewCount }: QualitySafetyCardProps) {
    return (
        <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="mb-4">Quality &amp; Safety</h3>
            <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                    <div>
                        <p className="text-green-900">False Negative Rate</p>
                        <p className="text-sm text-green-700 mt-1">Goal: 0%</p>
                    </div>
                    <p className="text-green-900">0%</p>
                </div>
                <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                    <div>
                        <p>Needs Review</p>
                        <p className="text-sm text-muted-foreground mt-1">Last 30 days</p>
                    </div>
                    <p>{needsReviewCount}</p>
                </div>
                <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                    <div>
                        <p>Evidence Highlights</p>
                        <p className="text-sm text-muted-foreground mt-1">
                            % with attached evidence
                        </p>
                    </div>
                    <p>98%</p>
                </div>
            </div>
        </div>
    );
}
