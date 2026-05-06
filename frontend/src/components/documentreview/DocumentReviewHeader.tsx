import { ArrowLeft, ArrowRight, FileText, Clock, ThumbsUp, ThumbsDown, SlidersHorizontal, MessageCircle, CheckCircle2, AlertTriangle } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { ReviewDocument } from '../../types/review-types';
import { submitReview } from '../../api/review-api';

function StatusBadge({ status }: { status: string }) {
    const s = status.toLowerCase();
    let cls = 'bg-yellow-50 text-yellow-700 border-yellow-200';
    let Icon = Clock;
    if (s === 'approved') { cls = 'bg-green-50 text-green-700 border-green-200'; Icon = CheckCircle2; }
    else if (s === 'rejected') { cls = 'bg-red-50 text-red-700 border-red-200'; Icon = AlertTriangle; }
    return (
        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-medium ${cls}`}>
            <Icon className="w-3 h-3" />
            {status}
        </span>
    );
}

interface DocumentReviewHeaderProps {
    doc: ReviewDocument;
    id: string | undefined;
    onOverride: () => void;
    onAskAI: () => void;
    onStatusChange?: (newStatus: string) => void;
    onPrev?: () => void;
    onNext?: () => void;
    hasPrev?: boolean;
    hasNext?: boolean;
    currentIndex?: number;
    totalCount?: number;
}

export function DocumentReviewHeader({ doc, id, onOverride, onAskAI, onStatusChange, onPrev, onNext, hasPrev, hasNext }: DocumentReviewHeaderProps) {
    const navigate = useNavigate();
    const [submitting, setSubmitting] = useState<'Approved' | 'Rejected' | null>(null);

    const handleQuickReview = async (status: 'Approved' | 'Rejected') => {
        if (!id || submitting) return;
        setSubmitting(status);
        try {
            const response = await submitReview(id, { status, justification: '' });
            onStatusChange?.(response.status);
        } finally {
            setSubmitting(null);
        }
    };

    return (
        <div className="bg-card border-b border-border flex">

            {/* LEFT COLUMN — matches PDF panel (flex-1) */}
            <div className="flex-1 px-6 py-4 flex flex-col gap-3">

                {/* Nav row: Back + Prev | Title | Next */}
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1 shrink-0">
                        <button
                            onClick={() => navigate('/')}
                            className="p-2 hover:bg-muted rounded-lg transition-colors"
                            title="Back to dashboard"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        <button
                            onClick={onPrev}
                            disabled={!hasPrev}
                            title="Previous document"
                            className="flex items-center gap-1.5 px-3 py-2 bg-muted hover:bg-muted/80 rounded-lg transition-colors text-sm font-medium disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            Prev
                        </button>
                    </div>

                    <div className="flex-1 flex flex-col items-center text-center min-w-0">
                        <div className="flex items-center gap-2">
                            <FileText className="w-5 h-5 text-muted-foreground shrink-0" />
                            <h2 className="truncate max-w-lg">{doc.name}</h2>
                        </div>
                        <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground flex-wrap justify-center">
                            <span>{doc.site}</span>
                            <span>•</span>
                            <span>{doc.ppmType}</span>
                        </div>
                    </div>

                    <div className="shrink-0">
                        <button
                            onClick={onNext}
                            disabled={!hasNext}
                            title="Next document"
                            className="flex items-center gap-1.5 px-3 py-2 bg-muted hover:bg-muted/80 rounded-lg transition-colors text-sm font-medium disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                            Next
                            <ArrowRight className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* Action row: Approve | Reject | Override */}
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => handleQuickReview('Approved')}
                        disabled={!!submitting}
                        title="Approve"
                        className="flex items-center gap-1.5 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <ThumbsUp className="w-4 h-4" />
                        {submitting === 'Approved' ? 'Saving…' : 'Approve'}
                    </button>
                    <button
                        onClick={() => handleQuickReview('Rejected')}
                        disabled={!!submitting}
                        title="Reject"
                        className="flex items-center gap-1.5 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <ThumbsDown className="w-4 h-4" />
                        {submitting === 'Rejected' ? 'Saving…' : 'Reject'}
                    </button>
                    <button
                        onClick={onOverride}
                        className="flex items-center gap-1.5 px-4 py-2 bg-muted rounded-lg hover:bg-muted/80 transition-colors text-sm font-medium shadow-sm"
                    >
                        <SlidersHorizontal className="w-4 h-4" />
                        Override
                    </button>
                    <button
                        onClick={onAskAI}
                        className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium shadow-sm"
                    >
                        <MessageCircle className="w-4 h-4" />
                        Ask AI
                    </button>
                </div>
            </div>

            {/* RIGHT COLUMN — matches Analysis panel (w-[480px]) */}
            <div className="w-[480px] px-6 py-4 flex flex-col justify-center gap-2">
                <div className="flex items-center gap-2 flex-wrap justify-end">
                    <StatusBadge status={doc.status} />
                    <span className="px-3 py-1 bg-red-50 text-red-700 rounded-full border border-red-200 text-sm">{doc.aiDecision}</span>
                    <span className="px-3 py-1 bg-orange-50 text-orange-700 rounded-full border border-orange-200 text-sm">Risk: {doc.riskLevel}</span>
                </div>
                <div className="flex items-center gap-3 justify-end">
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
                    <div className="flex items-center gap-1 text-sm text-muted-foreground">
                        <Clock className="w-4 h-4" />
                        <span>SLA: {doc.slaRemaining}</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
