export function RemedialDetectionCard() {
    return (
        <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="mb-4">Remedial Detection</h3>
            <div className="space-y-4">
                <div>
                    <label className="block mb-2 text-sm font-medium">Critical Keywords</label>
                    <textarea
                        rows={4}
                        defaultValue="immediate action, urgent repair, safety hazard, non-compliant, failure detected"
                        className="w-full px-4 py-2 bg-input-background rounded-lg border-0 focus:outline-none focus:ring-2 focus:ring-primary resize-none text-sm"
                    />
                    <p className="text-sm text-muted-foreground mt-2">
                        Comma-separated list of keywords that trigger critical remedial alerts
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <input
                        type="checkbox"
                        id="block-auto-approve"
                        className="rounded"
                        defaultChecked
                    />
                    <label htmlFor="block-auto-approve" className="text-sm">
                        Block auto-approval for any documents with remedial keywords
                    </label>
                </div>
            </div>
        </div>
    );
}
