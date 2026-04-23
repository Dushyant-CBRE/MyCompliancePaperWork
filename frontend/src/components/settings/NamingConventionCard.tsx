export function NamingConventionCard() {
    return (
        <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="mb-4">Naming Convention Rules</h3>
            <div className="space-y-4">
                <div>
                    <label className="block mb-2 text-sm font-medium">
                        Document Naming Pattern
                    </label>
                    <input
                        type="text"
                        defaultValue="{PPM_TYPE}_{SITE}_{DATE}.pdf"
                        className="w-full px-4 py-2 bg-input-background rounded-lg border-0 focus:outline-none focus:ring-2 focus:ring-primary font-mono text-sm"
                    />
                    <p className="text-sm text-muted-foreground mt-2">
                        Use placeholders: {'{PPM_TYPE}'}, {'{SITE}'}, {'{DATE}'}, {'{VENDOR}'}
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <input
                        type="checkbox"
                        id="enforce-naming"
                        className="rounded"
                        defaultChecked
                    />
                    <label htmlFor="enforce-naming" className="text-sm">
                        Flag documents that don&apos;t match naming convention
                    </label>
                </div>
            </div>
        </div>
    );
}
