import { StatCard } from '../StatCard';
import type { DashboardStats } from '../../types/document-types';

export type FilterKey = 'Approved' | 'Needs Review' | 'Rejected';

interface StatCardsProps {
    stats: DashboardStats;
    activeFilters?: FilterKey[];
    onFilterChange?: (filters: FilterKey[]) => void;
}

export function StatCards({ stats, activeFilters = [], onFilterChange }: StatCardsProps) {
    const total = stats.totalDocuments || 1;
    const statItems: { label: string; value: string; change: string; filter: FilterKey | null; color: 'blue' | 'green' | 'yellow' | 'red' }[] = [
        { label: 'Total Documents', value: String(stats.totalDocuments), change: '+0 today', filter: null, color: 'blue' },
        { label: 'Approved', value: String(stats.approved), change: `${Math.round(stats.approved / total * 100)}% rate`, filter: 'Approved', color: 'green' },
        { label: 'Needs Review', value: String(stats.needsReview), change: `${Math.round(stats.needsReview / total * 100)}% rate`, filter: 'Needs Review', color: 'yellow' },
        { label: 'Rejected', value: String(stats.rejected), change: `${Math.round(stats.rejected / total * 100)}% rate`, filter: 'Rejected', color: 'red' },
    ];

    const toggle = (filter: FilterKey | null) => {
        if (!filter) { onFilterChange?.([]); return; }
        const next = activeFilters.includes(filter)
            ? activeFilters.filter(f => f !== filter)
            : [...activeFilters, filter];
        onFilterChange?.(next);
    };

    return (
        <div className="grid grid-cols-4 gap-4 mb-6">
            {statItems.map((stat) => (
                <StatCard
                    key={stat.label}
                    label={stat.label}
                    value={stat.value}
                    change={stat.change}
                    selectedColor={stat.color}
                    isSelected={stat.filter ? activeFilters.includes(stat.filter) : activeFilters.length === 0}
                    onClick={() => toggle(stat.filter)}
                />
            ))}
        </div>
    );
}
