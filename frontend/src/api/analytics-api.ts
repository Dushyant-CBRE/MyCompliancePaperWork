import type { AnalyticsSummary } from '../types/document-types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL as string;

export async function getAnalytics(): Promise<AnalyticsSummary> {
    const res = await fetch(`${BASE_URL}/api/analytics`);

    if (!res.ok) {
        const body = await res.json().catch(() => ({})) as { detail?: string };
        throw new Error(body.detail ?? `Analytics fetch failed (${res.status})`);
    }

    return res.json() as Promise<AnalyticsSummary>;
}
