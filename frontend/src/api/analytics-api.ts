import type { AnalyticsSummary } from '../types/document-types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export async function getAnalytics(): Promise<AnalyticsSummary> {
    const res = await fetch(`${API_BASE}/api/analytics`);

    if (!res.ok) {
        const body = await res.json().catch(() => ({})) as { detail?: string };
        throw new Error(body.detail ?? `Analytics fetch failed (${res.status})`);
    }

    return res.json() as Promise<AnalyticsSummary>;
}
