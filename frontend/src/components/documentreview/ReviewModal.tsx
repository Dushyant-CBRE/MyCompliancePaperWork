import { useState } from 'react';

interface ReviewModalProps {
    documentId: string;
    onClose: () => void;
    onSubmit: (status: 'Approved' | 'Rejected', justification: string) => Promise<void>;
}

export function ReviewModal({ documentId: _documentId, onClose, onSubmit }: ReviewModalProps) {
    const [status, setStatus] = useState<'Approved' | 'Rejected' | ''>('');
    const [justification, setJustification] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async () => {
        if (!status) return;
        setLoading(true);
        setError(null);
        try {
            await onSubmit(status, justification);
            onClose();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Submission failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-card rounded-lg p-6 max-w-lg w-full mx-4">
                <h3 className="mb-6">Submit Review</h3>

                <div className="space-y-4 mb-6">
                    <div>
                        <label className="block mb-2 text-sm font-medium">
                            Review Status <span className="text-destructive">*</span>
                        </label>
                        <select
                            value={status}
                            onChange={(e) => setStatus(e.target.value as 'Approved' | 'Rejected')}
                            className="w-full px-4 py-2 bg-input-background rounded-lg border-0 focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                        >
                            <option value="">Select a status...</option>
                            <option value="Approved">Approved</option>
                            <option value="Rejected">Rejected</option>
                        </select>
                    </div>

                    <div>
                        <label className="block mb-2 text-sm font-medium">
                            Review Justification
                        </label>
                        <textarea
                            rows={4}
                            value={justification}
                            onChange={(e) => setJustification(e.target.value)}
                            placeholder="Provide justification for your review decision..."
                            className="w-full px-4 py-2 bg-input-background rounded-lg border-0 focus:outline-none focus:ring-2 focus:ring-primary resize-none text-sm"
                        />
                    </div>
                </div>

                {error && (
                    <p className="text-sm text-destructive mb-4">{error}</p>
                )}

                <div className="flex gap-3">
                    <button
                        onClick={onClose}
                        disabled={loading}
                        className="flex-1 px-4 py-2 bg-muted rounded-lg hover:bg-muted/80 transition-colors text-sm disabled:opacity-50"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={!status || loading}
                        className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Submitting...' : 'Submit'}
                    </button>
                </div>
            </div>
        </div>
    );
}
