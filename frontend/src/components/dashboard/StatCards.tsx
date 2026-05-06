import { StatCard } from '../StatCard';
import type { DashboardStats } from '../../types/document-types';

interface StatCardsProps {
    stats: DashboardStats;
}

export function StatCards({ stats }: StatCardsProps) {
    const total = stats.totalDocuments || 1; // avoid division by zero
    const statItems = [
        { label: 'Total Documents', value: String(stats.totalDocuments), change: '+0 today' },
        { label: 'Approved', value: String(stats.approved), change: `${Math.round(stats.approved / total * 100)}% rate` },
        { label: 'Needs Review', value: String(stats.needsReview), change: `${Math.round(stats.needsReview / total * 100)}% rate` },
        { label: 'Rejected', value: String(stats.rejected), change: `${Math.round(stats.rejected / total * 100)}% rate` },
    ];

    return (
        <div className="grid grid-cols-4 gap-4 mb-6">
            {statItems.map((stat) => (
                <StatCard key={stat.label} {...stat} />
            ))}
        </div>
    );
}
