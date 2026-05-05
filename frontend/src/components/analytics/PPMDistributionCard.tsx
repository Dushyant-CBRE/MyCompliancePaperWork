interface PPMDistributionCardProps {
    data: { type: string; count: number }[];
}

export function PPMDistributionCard({ data }: PPMDistributionCardProps) {
    const total = data.reduce((sum, d) => sum + d.count, 0) || 1;
    const COLORS = [
        'bg-primary', 'bg-accent', 'bg-yellow-500', 'bg-blue-500',
        'bg-purple-500', 'bg-pink-500', 'bg-orange-500',
    ];
    return (
        <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="mb-4">PPM Type Distribution</h3>
            <div className="space-y-3">
                {data.map((ppm, idx) => (
                    <div key={ppm.type}>
                        <div className="flex items-center justify-between mb-1 text-sm">
                            <span>{ppm.type}</span>
                            <span className="text-muted-foreground">{ppm.count}</span>
                        </div>
                        <div className="bg-muted rounded-full h-2">
                            <div
                                className={`h-full rounded-full ${COLORS[idx % COLORS.length]}`}
                                style={{ width: `${(ppm.count / total) * 100}%` }}
                            />
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
