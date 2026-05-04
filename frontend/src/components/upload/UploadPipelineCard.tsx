import { FileText, CheckCircle, Loader2 } from 'lucide-react';
import { PIPELINE_STAGES } from '../../lib/constants';
import type { Stage } from '../../lib/constants';

interface UploadPipelineCardProps {
    currentStage: Stage | null;
    filename: string;
    fileSize: string;
    onOpenReview: () => void;
}

export function UploadPipelineCard({ currentStage, filename, fileSize, onOpenReview }: UploadPipelineCardProps) {
    const currentIndex = currentStage ? PIPELINE_STAGES.indexOf(currentStage) : -1;

    return (
        <div className="mt-6 bg-card border border-border rounded-lg p-6">
            {/* File info row */}
            <div className="flex items-center gap-4 mb-6">
                <FileText className="w-8 h-8 text-primary flex-shrink-0" />
                <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{filename}</p>
                    <p className="text-sm text-muted-foreground mt-0.5">{fileSize}</p>
                </div>
            </div>

            {/* Stage list */}
            <div className="space-y-2">
                {PIPELINE_STAGES.map((stage, idx) => {
                    const isComplete = idx < currentIndex;
                    const isCurrent = idx === currentIndex;

                    return (
                        <div
                            key={stage}
                            className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                                isComplete
                                    ? 'bg-accent/10'
                                    : isCurrent
                                      ? 'bg-primary/10'
                                      : 'bg-muted/30'
                            }`}
                        >
                            {isComplete ? (
                                <CheckCircle className="w-5 h-5 text-accent flex-shrink-0" />
                            ) : isCurrent ? (
                                <Loader2 className="w-5 h-5 text-primary animate-spin flex-shrink-0" />
                            ) : (
                                <div className="w-5 h-5 rounded-full border-2 border-muted-foreground flex-shrink-0" />
                            )}
                            <span
                                className={`text-sm font-medium ${
                                    isComplete
                                        ? 'text-accent-foreground'
                                        : isCurrent
                                          ? 'text-primary'
                                          : 'text-muted-foreground'
                                }`}
                            >
                                {stage}
                            </span>
                        </div>
                    );
                })}
            </div>

            {/* Open Review CTA */}
            {currentStage === 'Completed' && (
                <button
                    onClick={onOpenReview}
                    className="w-full mt-4 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm font-medium"
                >
                    Open Review
                </button>
            )}
        </div>
    );
}
