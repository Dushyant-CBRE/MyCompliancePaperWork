import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Loader2, AlertCircle } from 'lucide-react';
import type { DocumentRecord } from '../types/document-types';
import { DocumentReviewHeader } from '../components/documentreview/DocumentReviewHeader';
import { PDFViewerPanel } from '../components/documentreview/PDFViewerPanel';
import { AnalysisPanel } from '../components/documentreview/AnalysisPanel';
import { OverrideModal } from '../components/documentreview/OverrideModal';
import { getDocumentById, overrideDocument, mapDocumentToReview } from '../api/document-review-api';

type TabId = 'fields' | 'validation' | 'remedial' | 'audit';

export function DocumentReview() {
    const { id } = useParams();
    const [record, setRecord] = useState<DocumentRecord | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<TabId>('fields');
    const [showOverrideModal, setShowOverrideModal] = useState(false);
    const [overrideLoading, setOverrideLoading] = useState(false);

    const fetchDocument = useCallback(async () => {
        if (!id) return;
        try {
            const data = await getDocumentById(id);
            setRecord(data);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch document');
        } finally {
            setLoading(false);
        }
    }, [id]);

    useEffect(() => {
        fetchDocument();
    }, [fetchDocument]);

    const handleOverride = async (decision: 'approved' | 'rejected', reason: string) => {
        if (!id) return;
        setOverrideLoading(true);
        try {
            const updated = await overrideDocument(id, {
                decision,
                reason,
                officer_name: 'Compliance Officer',
            });
            setRecord(updated);
            setShowOverrideModal(false);
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Override failed');
        } finally {
            setOverrideLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
        );
    }

    if (error || !record) {
        return (
            <div className="h-full flex items-center justify-center">
                <div className="text-center">
                    <AlertCircle className="w-12 h-12 text-destructive mx-auto mb-4" />
                    <p className="text-lg font-medium">Failed to load document</p>
                    <p className="text-muted-foreground mt-1">{error || 'Document not found'}</p>
                </div>
            </div>
        );
    }

    const { doc, fields, checks, evidence, auditData, pdfUrl } = mapDocumentToReview(record);

    return (
        <div className="h-full flex flex-col">
            <DocumentReviewHeader
                doc={doc}
                id={id}
                onOverride={() => setShowOverrideModal(true)}
            />

            <div className="flex-1 flex overflow-hidden">
                <PDFViewerPanel fileName={doc.name} pdfUrl={pdfUrl} />
                <AnalysisPanel
                    activeTab={activeTab}
                    onTabChange={setActiveTab}
                    fields={fields}
                    checks={checks}
                    evidence={evidence}
                    auditData={auditData}
                />
            </div>

            {showOverrideModal && (
                <OverrideModal
                    onClose={() => setShowOverrideModal(false)}
                    onSubmit={handleOverride}
                    isLoading={overrideLoading}
                />
            )}
        </div>
    );
}
