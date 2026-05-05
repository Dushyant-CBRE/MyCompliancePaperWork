import { StatCard } from '../StatCard';
import type { DashboardStats } from '../../types/document-types';

interface StatCardsProps {
    stats: DashboardStats;
}

export function StatCards({ stats }: StatCardsProps) {
    const total = stats.totalDocuments || 1; // avoid division by zero
    const statItems = [
        { label: 'Total Documents', value: String(stats.totalDocuments), change: '+0 today' },
        { label: 'Auto-Approved', value: String(stats.autoApproved), change: `${Math.round(stats.autoApproved / total * 100)}% rate` },
        { label: 'Needs Review', value: String(stats.needsReview), change: `${Math.round(stats.needsReview / total * 100)}% rate` },
        { label: 'Remedial Detected', value: String(stats.remedialDetected), change: `Critical: ${stats.criticalCount}` },
    ];

    return (
        <div className="grid grid-cols-4 gap-4 mb-6">
            {statItems.map((stat) => (
                <StatCard key={stat.label} {...stat} />
            ))}
        </div>
    );
}
