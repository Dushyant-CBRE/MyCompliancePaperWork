import { useState } from 'react';
import { Loader2 } from 'lucide-react';

interface OverrideModalProps {
    onClose: () => void;
    onSubmit: (decision: 'approved' | 'rejected', reason: string) => void;
    isLoading?: boolean;
    lockedDecision?: 'rejected';
}

export function OverrideModal({ onClose, onSubmit, isLoading = false, lockedDecision }: OverrideModalProps) {
    const [comments, setComments] = useState('');
    const [decision, setDecision] = useState<'approved' | 'rejected'>(lockedDecision ?? 'approved');

    const canSubmit = !isLoading;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-card rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-auto">
                <h3 className="mb-4">{lockedDecision === 'rejected' ? 'Reject Document' : 'Override AI Decision'}</h3>

                <div className="space-y-4 mb-6">
                    <div>
                        <label className="block mb-2 text-sm font-medium">Decision</label>
                        <div className="flex gap-3">
                            <button
                                onClick={() => !lockedDecision && setDecision('approved')}
                                disabled={!!lockedDecision}
                                className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                                    decision === 'approved'
                                        ? 'bg-green-100 text-green-800 border-2 border-green-300'
                                        : 'bg-muted'
                                } disabled:opacity-40 disabled:cursor-not-allowed`}
                            >
                                Approve
                            </button>
                            <button
                                onClick={() => !lockedDecision && setDecision('rejected')}
                                disabled={!!lockedDecision}
                                className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                                    decision === 'rejected'
                                        ? 'bg-red-100 text-red-800 border-2 border-red-300'
                                        : 'bg-muted hover:bg-muted/80'
                                } disabled:cursor-default`}
                            >
                                Reject
                            </button>
                        </div>
                    </div>

                    <div>
                        <label className="block mb-2 text-sm font-medium">Comments</label>
                        <textarea
                            rows={4}
                            value={comments}
                            onChange={(e) => setComments(e.target.value)}
                            placeholder="Provide detailed reasoning for this override..."
                            className="w-full px-4 py-2 bg-input-background rounded-lg border-0 focus:outline-none focus:ring-2 focus:ring-primary resize-none text-sm"
                        />
                    </div>

                </div>

                <div className="flex gap-3">
                    <button
                        onClick={onClose}
                        disabled={isLoading}
                        className="flex-1 px-4 py-2 bg-muted rounded-lg hover:bg-muted/80 transition-colors text-sm disabled:opacity-50"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={() => canSubmit && onSubmit(decision, comments)}
                        disabled={!canSubmit}
                        className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                        {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
                        {isLoading ? 'Submitting...' : 'Submit Override'}
                    </button>
                </div>
            </div>
        </div>
    );
}
