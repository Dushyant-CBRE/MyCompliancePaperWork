import { ArrowLeft, FileText, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { ReviewDocument } from '../../types';

interface DocumentReviewHeaderProps {
    doc: ReviewDocument;
    id: string | undefined;
    onOverride: () => void;
}

export function DocumentReviewHeader({ doc, id, onOverride }: DocumentReviewHeaderProps) {
    const navigate = useNavigate();

    return (
        <div className="bg-card border-b border-border px-6 py-4">
            <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => navigate('/')}
                        className="p-2 hover:bg-muted rounded-lg transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <div className="flex items-center gap-3">
                            <FileText className="w-5 h-5 text-muted-foreground" />
                            <h2>{doc.name}</h2>
                        </div>
                        <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                            <span>{doc.site}</span>
                            <span>•</span>
                            <span>{doc.ppmType}</span>
                            <span>•</span>
                            <span>Document ID: {id}</span>
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <div className="text-right">
                        <div className="flex items-center gap-2 justify-end">
                            <span className="px-3 py-1 bg-red-50 text-red-700 rounded-full border border-red-200 text-sm">
                                {doc.aiDecision}
                            </span>
                            <span className="px-3 py-1 bg-orange-50 text-orange-700 rounded-full border border-orange-200 text-sm">
                                Risk: {doc.riskLevel}
                            </span>
                        </div>
                        <div className="flex items-center gap-2 mt-2 text-sm text-muted-foreground justify-end">
                            <Clock className="w-4 h-4" />
                            <span>SLA: {doc.slaRemaining}</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-3">
                <button className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm">
                    Approve
                </button>
                <button
                    onClick={onOverride}
                    className="px-6 py-2 bg-muted rounded-lg hover:bg-muted/80 transition-colors text-sm"
                >
                    Override
                </button>
                <button className="px-6 py-2 bg-muted rounded-lg hover:bg-muted/80 transition-colors text-sm">
                    Request Resubmission
                </button>
                <button className="px-6 py-2 bg-destructive text-primary-foreground rounded-lg hover:bg-destructive/90 transition-colors text-sm">
                    Reject
                </button>
                <div className="flex-1" />
                <div className="flex items-center gap-2 px-4 py-2 bg-muted rounded-lg">
                    <span className="text-sm">Confidence:</span>
                    <div className="w-24 bg-background rounded-full h-2">
                        <div
                            className="h-full rounded-full bg-yellow-400"
                            style={{ width: `${doc.confidence}%` }}
                        />
                    </div>
                    <span className="text-sm">{doc.confidence}%</span>
                </div>
            </div>
        </div>
    );
}
