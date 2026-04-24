const ppmTypes = [
    { type: 'Fire Safety', count: 89, color: 'bg-primary' },
    { type: 'Electrical', count: 67, color: 'bg-accent' },
    { type: 'HVAC', count: 54, color: 'bg-yellow-500' },
    { type: 'Elevator', count: 38, color: 'bg-blue-500' },
];

const TOTAL = 248;

export function PPMDistributionCard() {
    return (
        <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="mb-4">PPM Type Distribution</h3>
            <div className="space-y-3">
                {ppmTypes.map((ppm) => (
                    <div key={ppm.type}>
                        <div className="flex items-center justify-between mb-1 text-sm">
                            <span>{ppm.type}</span>
                            <span className="text-muted-foreground">{ppm.count}</span>
                        </div>
                        <div className="bg-muted rounded-full h-2">
                            <div
                                className={`h-full rounded-full ${ppm.color}`}
                                style={{ width: `${(ppm.count / TOTAL) * 100}%` }}
                            />
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
