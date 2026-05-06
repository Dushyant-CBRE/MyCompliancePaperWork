import type { AnalyticsSummary } from '../types/document-types';

export async function getAnalytics(): Promise<AnalyticsSummary> {
    const res = await fetch(`/api/analytics`);

    if (!res.ok) {
        const body = await res.json().catch(() => ({})) as { detail?: string };
        throw new Error(body.detail ?? `Analytics fetch failed (${res.status})`);
    }

    return res.json() as Promise<AnalyticsSummary>;
}
