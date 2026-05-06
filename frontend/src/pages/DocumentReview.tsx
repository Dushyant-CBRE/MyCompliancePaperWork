import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import type { ExtractedField, ValidationCheck, RemedialEvidence, ReviewDocument } from '../types/review-types';
import { DocumentReviewHeader } from '../components/documentreview/DocumentReviewHeader';
import { PDFViewerPanel } from '../components/documentreview/PDFViewerPanel';
import { AnalysisPanel } from '../components/documentreview/AnalysisPanel';
import { OverrideModal } from '../components/documentreview/OverrideModal';
import { ReviewModal } from '../components/documentreview/ReviewModal';
import { getDocumentForReview, getPdfObjectUrl, submitReview } from '../api/review-api';

type TabId = 'fields' | 'validation' | 'remedial' | 'audit';

export function DocumentReview() {
    const { id } = useParams();
    const [activeTab, setActiveTab] = useState<TabId>('fields');
    const [showOverrideModal, setShowOverrideModal] = useState(false);
    const [showReviewModal, setShowReviewModal] = useState(false);

    const [doc, setDoc] = useState<ReviewDocument | null>(null);
    const [fields, setFields] = useState<ExtractedField[]>([]);
    const [checks, setChecks] = useState<ValidationCheck[]>([]);
    const [evidence, setEvidence] = useState<RemedialEvidence[]>([]);
    const [pdfObjectUrl, setPdfObjectUrl] = useState<string | null>(null);
    const [pdfLoading, setPdfLoading] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!id) return;
        setLoading(true);
        setError(null);
        getDocumentForReview(id)
            .then(({ doc, fields, checks, evidence }) => {
                setDoc(doc);
                setFields(fields);
                setChecks(checks);
                setEvidence(evidence);
            })
            .catch((err: unknown) => {
                setError(err instanceof Error ? err.message : 'Failed to load document.');
            })
            .finally(() => setLoading(false));
    }, [id]);

    // Fetch PDF bytes via backend proxy (keeps Azure credentials server-side)
    useEffect(() => {
        if (!id) return;
        let objectUrl: string | null = null;
        setPdfLoading(true);
        getPdfObjectUrl(id)
            .then((url) => {
                objectUrl = url;
                setPdfObjectUrl(url);
            })
            .catch(() => {
                // Non-fatal: viewer shows placeholder if PDF unavailable
                setPdfObjectUrl(null);
            })
            .finally(() => setPdfLoading(false));
        return () => {
            if (objectUrl) URL.revokeObjectURL(objectUrl);
        };
    }, [id]);

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center text-muted-foreground text-sm">
                Loading document…
            </div>
        );
    }

    if (error || !doc) {
        return (
            <div className="h-full flex items-center justify-center text-destructive text-sm">
                {error ?? 'Document not found.'}
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col">
            <DocumentReviewHeader
                doc={doc}
                id={id}
                onOverride={() => setShowOverrideModal(true)}
                onReview={() => setShowReviewModal(true)}
            />

            <div className="flex-1 flex overflow-hidden">
                <PDFViewerPanel fileName={doc.name} blobUrl={pdfObjectUrl} pdfLoading={pdfLoading} />
                <AnalysisPanel
                    activeTab={activeTab}
                    onTabChange={setActiveTab}
                    fields={fields}
                    checks={checks}
                    evidence={evidence}
                />
            </div>

            {showOverrideModal && (
                <OverrideModal onClose={() => setShowOverrideModal(false)} />
            )}

            {showReviewModal && (
                <ReviewModal
                    documentId={id ?? ''}
                    onClose={() => setShowReviewModal(false)}
                    onSubmit={async (status, justification) => {
                        await submitReview(id ?? '', { status, justification });
                    }}
                />
            )}
        </div>
    );
}
