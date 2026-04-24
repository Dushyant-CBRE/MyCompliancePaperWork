export function ExceptionStatCards() {
    return (
        <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-card border border-border rounded-lg p-4">
                <p className="text-sm text-muted-foreground">Critical Items</p>
                <p className="text-3xl font-bold mt-1">1</p>
                <p className="text-sm text-red-600 mt-1">Immediate attention required</p>
            </div>
            <div className="bg-card border border-border rounded-lg p-4">
                <p className="text-sm text-muted-foreground">Unassigned</p>
                <p className="text-3xl font-bold mt-1">2</p>
                <p className="text-sm text-muted-foreground mt-1">Awaiting assignment</p>
            </div>
            <div className="bg-card border border-border rounded-lg p-4">
                <p className="text-sm text-muted-foreground">SLA Breach Risk</p>
                <p className="text-3xl font-bold mt-1">1</p>
                <p className="text-sm text-orange-600 mt-1">Within 2 hours</p>
            </div>
        </div>
    );
}
