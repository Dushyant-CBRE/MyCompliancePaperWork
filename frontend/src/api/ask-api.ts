const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export interface CitedSource {
    chunk_index: number;
    text: string;
    relevance_score: number;
}

export interface AskResponse {
    question: string;
    answer: string;
    sources: CitedSource[];
    document_id: string;
}

export async function askDocument(documentId: string, question: string): Promise<AskResponse> {
    const res = await fetch(`${API_BASE}/api/documents/${documentId}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
    });
    if (!res.ok) {
        const data = await res.json().catch(() => ({})) as { detail?: string };
        throw new Error(data.detail ?? `Ask failed (${res.status})`);
    }
    return res.json() as Promise<AskResponse>;
}
