import { AlertTriangle, Loader2 } from 'lucide-react';

interface BatchApproveModalProps {
    eligibleCount: number;
    isLoading?: boolean;
    onClose: () => void;
    onConfirm: () => void;
}

export function BatchApproveModal({ eligibleCount, isLoading = false, onClose, onConfirm }: BatchApproveModalProps) {
    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-card rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
                <h3 className="mb-4">Batch Approve Confirmation</h3>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                    <div className="flex gap-3">
                        <AlertTriangle className="w-5 h-5 text-yellow-700 flex-shrink-0 mt-0.5" />
                        <div>
                            <p className="text-sm text-yellow-800">
                                You are about to approve{' '}
                                <span className="font-semibold">{eligibleCount} documents</span>{' '}
                                with confidence ≥85%.
                            </p>
                            <p className="text-sm text-yellow-800 mt-2">
                                This action will skip individual remedial action review. Ensure all
                                documents have been validated.
                            </p>
                        </div>
                    </div>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={onClose}
                        disabled={isLoading}
                        className="flex-1 px-4 py-2 bg-muted rounded-lg hover:bg-muted/80 transition-colors text-sm font-medium disabled:opacity-50"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={onConfirm}
                        disabled={isLoading}
                        className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm font-medium disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                        {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
                        {isLoading ? 'Approving...' : 'Approve All'}
                    </button>
                </div>
            </div>
        </div>
    );
}
