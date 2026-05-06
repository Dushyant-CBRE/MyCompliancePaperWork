import type { ReviewRequest, ReviewResponse } from '../types/review-types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL as string;

export async function submitReview(
    documentId: string,
    body: ReviewRequest,
): Promise<ReviewResponse> {
    const res = await fetch(`${BASE_URL}/api/documents/${documentId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const data = await res.json().catch(() => ({})) as { detail?: string };
        throw new Error(data.detail ?? `Review submission failed (${res.status})`);
    }

    return res.json() as Promise<ReviewResponse>;
}
