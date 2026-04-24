interface OverrideModalProps {
    onClose: () => void;
}

export function OverrideModal({ onClose }: OverrideModalProps) {
    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-card rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-auto">
                <h3 className="mb-4">Override AI Decision</h3>

                <div className="space-y-4 mb-6">
                    <div>
                        <label className="block mb-2 text-sm font-medium">
                            Reason for Override
                        </label>
                        <select className="w-full px-4 py-2 bg-input-background rounded-lg border-0 focus:outline-none focus:ring-2 focus:ring-primary text-sm">
                            <option>Select a reason...</option>
                            <option>Incorrect site</option>
                            <option>Wrong date</option>
                            <option>Missing signatures</option>
                            <option>Incorrect PPM type</option>
                            <option>Remedial misclassified</option>
                            <option>Other</option>
                        </select>
                    </div>

                    <div>
                        <label className="block mb-2 text-sm font-medium">Comments</label>
                        <textarea
                            rows={4}
                            placeholder="Provide detailed reasoning for this override..."
                            className="w-full px-4 py-2 bg-input-background rounded-lg border-0 focus:outline-none focus:ring-2 focus:ring-primary resize-none text-sm"
                        />
                    </div>

                    <div className="flex items-center gap-2">
                        <input type="checkbox" id="training-feedback" className="rounded" />
                        <label htmlFor="training-feedback" className="text-sm">
                            Mark as training feedback to improve AI accuracy
                        </label>
                    </div>
                </div>

                <div className="flex gap-3">
                    <button
                        onClick={onClose}
                        className="flex-1 px-4 py-2 bg-muted rounded-lg hover:bg-muted/80 transition-colors text-sm"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={onClose}
                        className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm"
                    >
                        Submit Override
                    </button>
                </div>
            </div>
        </div>
    );
}
