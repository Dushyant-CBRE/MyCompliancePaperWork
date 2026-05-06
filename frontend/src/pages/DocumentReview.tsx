import { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import type { ExtractedField, ValidationCheck, RemedialEvidence, ReviewDocument } from '../types/review-types';
import { DocumentReviewHeader } from '../components/documentreview/DocumentReviewHeader';
import { PDFViewerPanel } from '../components/documentreview/PDFViewerPanel';
import { AnalysisPanel } from '../components/documentreview/AnalysisPanel';
import { OverrideModal } from '../components/documentreview/OverrideModal';
import { getDocumentForReview, getPdfObjectUrl } from '../api/review-api';
import { getDocuments } from '../api/dashboard-api';

type TabId = 'fields' | 'validation' | 'remedial' | 'audit';

export function DocumentReview() {
    const { id } = useParams();
    const navigate = useNavigate();
    const location = useLocation();

    const [activeTab, setActiveTab] = useState<TabId>('fields');
    const [showOverrideModal, setShowOverrideModal] = useState(false);

    // ID list for prev/next — comes from router state or is fetched as fallback
    const [ids, setIds] = useState<string[]>((location.state as { ids?: string[] } | null)?.ids ?? []);

    const currentIndex = ids.indexOf(id ?? '');
    const hasPrev = currentIndex > 0;
    const hasNext = currentIndex !== -1 && currentIndex < ids.length - 1;

    const goTo = (targetId: string) => navigate(`/document/${targetId}`, { state: { ids } });

    const [doc, setDoc] = useState<ReviewDocument | null>(null);
    const [fields, setFields] = useState<ExtractedField[]>([]);
    const [checks, setChecks] = useState<ValidationCheck[]>([]);
    const [evidence, setEvidence] = useState<RemedialEvidence[]>([]);
    const [pdfObjectUrl, setPdfObjectUrl] = useState<string | null>(null);
    const [pdfLoading, setPdfLoading] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // If no ID list was passed (e.g. direct URL access), fetch all documents to build the list
    useEffect(() => {
        if (ids.length > 0) return;
        getDocuments(undefined, 200)
            .then((res) => {
                const allIds = res.documents.map((r) => r.document_id);
                setIds(allIds);
            })
            .catch(() => { /* non-fatal */ });
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        if (!id) return;
        setLoading(true);
        setError(null);
        setDoc(null);
        setFields([]);
        setChecks([]);
        setEvidence([]);
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
                onStatusChange={(newStatus) => setDoc((prev) => prev ? { ...prev, status: newStatus } : prev)}
                hasPrev={hasPrev}
                hasNext={hasNext}
                onPrev={() => hasPrev && goTo(ids[currentIndex - 1])}
                onNext={() => hasNext && goTo(ids[currentIndex + 1])}
                currentIndex={currentIndex !== -1 ? currentIndex : undefined}
                totalCount={ids.length > 0 ? ids.length : undefined}
            />

            <div className="flex-1 flex overflow-hidden">
                <PDFViewerPanel fileName={doc.name} blobUrl={pdfObjectUrl} pdfLoading={pdfLoading} />
                <AnalysisPanel
                    activeTab={activeTab}
                    onTabChange={setActiveTab}
                    fields={fields}
                    checks={checks}
                    evidence={evidence} 
                    auditData={undefined}                
                />
            </div>

            {showOverrideModal && (
                <OverrideModal onClose={() => setShowOverrideModal(false)} 
                onSubmit={() => {}}/>
            )}
        </div>
    );
}