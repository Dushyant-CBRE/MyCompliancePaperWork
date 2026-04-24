interface StatCardProps {
    label: string;
    value: string;
    change: string;
}

export function StatCard({ label, value, change }: StatCardProps) {
    return (
        <div className="bg-card border border-border rounded-lg p-4">
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="text-3xl font-bold mt-1">{value}</p>
            <p className="text-sm text-muted-foreground mt-1">{change}</p>
        </div>
    );
}
