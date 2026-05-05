import { useEffect, useState } from 'react';
import { PageHeader } from '../components/PageHeader';
import { AnalyticsStatCards } from '../components/analytics/AnalyticsStatCards';
import { ProcessingLineChart } from '../components/analytics/ProcessingLineChart';
import { ConfidenceBarChart } from '../components/analytics/ConfidenceBarChart';
import { SiteBreakdownTable } from '../components/analytics/SiteBreakdownTable';
import { QualitySafetyCard } from '../components/analytics/QualitySafetyCard';
import { PPMDistributionCard } from '../components/analytics/PPMDistributionCard';
import { getAnalytics } from '../api/analytics-api';
import type { AnalyticsSummary } from '../types/document-types';

function formatProcessingTime(seconds: number): string {
    if (seconds <= 0) return '—';
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

export function Analytics() {
    const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        getAnalytics()
            .then(setSummary)
            .catch((err: unknown) =>
                setError(err instanceof Error ? err.message : 'Failed to load analytics'),
            );
    }, []);

    const overrideRate =
        summary && summary.total_documents > 0
            ? Math.max(0, (summary.approved / summary.total_documents) * 100)
            : 0;

    return (
        <div className="p-6">
            <PageHeader
                title="Analytics & Accuracy"
                subtitle="System performance and quality metrics"
            />
            {error && (
                <div className="mb-4 p-4 bg-destructive/10 border border-destructive/30 rounded-lg text-sm text-destructive">
                    {error}
                </div>
            )}
            <AnalyticsStatCards
                autoApproveRate={summary?.auto_approval_rate ?? 0}
                criticalAlerts={summary?.remedial_critical ?? 0}
                overrideRate={overrideRate}
                avgProcessingTime={formatProcessingTime(summary?.avg_processing_time_seconds ?? 0)}
            />
            <div className="grid grid-cols-2 gap-6 mb-6">
                <ProcessingLineChart data={summary?.processing_buckets ?? []} />
                <ConfidenceBarChart data={summary?.confidence_distribution ?? []} />
            </div>
            <div className="mb-6">
                <SiteBreakdownTable data={summary?.site_breakdown ?? []} />
            </div>
            <div className="grid grid-cols-2 gap-6">
                <QualitySafetyCard criticalRemedial={summary?.remedial_critical ?? 0} />
                <PPMDistributionCard data={summary?.ppm_distribution ?? []} />
            </div>
        </div>
    );
}
