import { StatCard } from '../StatCard';

const stats = [
    { label: 'Total Documents', value: '248', change: '+12 today' },
    { label: 'Auto-Approved', value: '186', change: '75% rate' },
    { label: 'Needs Review', value: '42', change: '17% rate' },
    { label: 'Remedial Detected', value: '8', change: 'Critical: 2' },
];

export function StatCards() {
    return (
        <div className="grid grid-cols-4 gap-4 mb-6">
            {stats.map((stat) => (
                <StatCard key={stat.label} {...stat} />
            ))}
        </div>
    );
}
