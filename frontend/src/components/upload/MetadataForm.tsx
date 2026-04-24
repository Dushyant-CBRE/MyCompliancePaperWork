export function MetadataForm() {
    return (
        <div className="mt-8 bg-card border border-border rounded-lg p-6">
            <h3 className="mb-1">Optional Metadata</h3>
            <p className="text-sm text-muted-foreground mb-6">
                AI will auto-extract these fields, but you can provide them manually for higher
                accuracy
            </p>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium mb-2">Site</label>
                    <select className="w-full px-4 py-2 bg-input-background rounded-lg border-0 text-sm focus:outline-none focus:ring-2 focus:ring-primary">
                        <option>Auto-detect</option>
                        <option>DLF Cyber City</option>
                        <option>Udyog Vihar</option>
                        <option>Golf Course Rd</option>
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium mb-2">PPM Type</label>
                    <select className="w-full px-4 py-2 bg-input-background rounded-lg border-0 text-sm focus:outline-none focus:ring-2 focus:ring-primary">
                        <option>Auto-detect</option>
                        <option>Fire Safety</option>
                        <option>Electrical</option>
                        <option>HVAC</option>
                        <option>Elevator</option>
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium mb-2">Vendor</label>
                    <input
                        type="text"
                        placeholder="Auto-detect"
                        className="w-full px-4 py-2 bg-input-background rounded-lg border-0 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium mb-2">Document Date</label>
                    <input
                        type="date"
                        className="w-full px-4 py-2 bg-input-background rounded-lg border-0 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                </div>
            </div>

            <div className="mt-5 flex items-center gap-2">
                <input type="checkbox" id="smartsheet" className="rounded" />
                <label htmlFor="smartsheet" className="text-sm">
                    Mark as &ldquo;Imported from Smartsheet&rdquo; (Demo mode)
                </label>
            </div>
        </div>
    );
}
