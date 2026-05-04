export interface MetadataValues {
    expected_site_name: string;
    expected_ppm_type: string;
    expected_document_date: string;
    expected_vendor_name: string;
    smartsheet: boolean;
}

interface MetadataFormProps {
    values: MetadataValues;
    onChange: (values: MetadataValues) => void;
}

export function MetadataForm({ values, onChange }: MetadataFormProps) {
    const set = <K extends keyof MetadataValues>(key: K, val: MetadataValues[K]) =>
        onChange({ ...values, [key]: val });

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
                    <select
                        value={values.expected_site_name}
                        onChange={(e) => set('expected_site_name', e.target.value)}
                        className="w-full px-4 py-2 bg-input-background rounded-lg border-0 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                        <option value="">Auto-detect</option>
                        <option value="DLF Cyber City">DLF Cyber City</option>
                        <option value="Udyog Vihar">Udyog Vihar</option>
                        <option value="Golf Course Rd">Golf Course Rd</option>
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium mb-2">PPM Type</label>
                    <select
                        value={values.expected_ppm_type}
                        onChange={(e) => set('expected_ppm_type', e.target.value)}
                        className="w-full px-4 py-2 bg-input-background rounded-lg border-0 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                        <option value="">Auto-detect</option>
                        <option value="Fire Safety">Fire Safety</option>
                        <option value="Electrical">Electrical</option>
                        <option value="HVAC">HVAC</option>
                        <option value="Elevator">Elevator</option>
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium mb-2">Vendor</label>
                    <input
                        type="text"
                        placeholder="Auto-detect"
                        value={values.expected_vendor_name}
                        onChange={(e) => set('expected_vendor_name', e.target.value)}
                        className="w-full px-4 py-2 bg-input-background rounded-lg border-0 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium mb-2">Document Date</label>
                    <input
                        type="date"
                        value={values.expected_document_date}
                        onChange={(e) => set('expected_document_date', e.target.value)}
                        className="w-full px-4 py-2 bg-input-background rounded-lg border-0 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                </div>
            </div>

            <div className="mt-5 flex items-center gap-2">
                <input
                    type="checkbox"
                    id="smartsheet"
                    className="rounded"
                    checked={values.smartsheet}
                    onChange={(e) => set('smartsheet', e.target.checked)}
                />
                <label htmlFor="smartsheet" className="text-sm">
                    Mark as &ldquo;Imported from Smartsheet&rdquo; (Demo mode)
                </label>
            </div>
        </div>
    );
}
