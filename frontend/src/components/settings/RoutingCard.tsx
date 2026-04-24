export function RoutingCard() {
    return (
        <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="mb-4">Routing Destinations</h3>
            <div className="space-y-4">
                <div>
                    <label className="block mb-2 text-sm font-medium">
                        Auto-Approved Documents
                    </label>
                    <select className="w-full px-4 py-2 bg-input-background rounded-lg border-0 focus:outline-none focus:ring-2 focus:ring-primary text-sm">
                        <option>Send to Smartsheet (Primary)</option>
                        <option>Send to SharePoint</option>
                        <option>Send to Document Management System</option>
                        <option>Custom API Endpoint</option>
                    </select>
                </div>
                <div>
                    <label className="block mb-2 text-sm font-medium">Rejected Documents</label>
                    <select className="w-full px-4 py-2 bg-input-background rounded-lg border-0 focus:outline-none focus:ring-2 focus:ring-primary text-sm">
                        <option>Send rejection email to vendor</option>
                        <option>Create task in Project Management System</option>
                        <option>Archive to Rejected folder</option>
                    </select>
                </div>
            </div>
        </div>
    );
}
