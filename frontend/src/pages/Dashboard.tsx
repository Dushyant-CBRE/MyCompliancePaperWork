import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload } from 'lucide-react';
import type { Document, DocumentRecord, DashboardStats } from '../types/document-types';
import { PageHeader } from '../components/PageHeader';
import { StatCards } from '../components/dashboard/StatCards';
import { ProcessingPipeline } from '../components/dashboard/ProcessingPipeline';
import { DocumentsTable } from '../components/dashboard/DocumentsTable';
import { BatchApproveModal } from '../components/dashboard/BatchApproveModal';
import { getDocuments, overrideDocument, mapDocumentRecord } from '../api/dashboard-api';

export function Dashboard() {
    const navigate = useNavigate();
    const [documents, setDocuments] = useState<Document[]>([]);
    const [rawRecords, setRawRecords] = useState<DocumentRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showBatchModal, setShowBatchModal] = useState(false);
    const [batchLoading, setBatchLoading] = useState(false);
    const [hoveredStatus, setHoveredStatus] = useState<string | null>(null);

    const fetchDocuments = useCallback(async () => {
        try {
            const response = await getDocuments(undefined, 50);
            setRawRecords(response.documents);
            setDocuments(response.documents.map(mapDocumentRecord));
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load documents');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchDocuments();
    }, [fetchDocuments]);

    const stats: DashboardStats = {
        totalDocuments: rawRecords.length,
        approved: rawRecords.filter(r => r.status === 'auto_approved' || r.status === 'approved').length,
        needsReview: rawRecords.filter(r => r.status === 'manual_review' || r.status === 'requires_attention' || r.status === 'pending' || r.status === 'processing').length,
        rejected: rawRecords.filter(r => r.status === 'rejected').length,
    };

    const eligibleCount = documents.filter(d => d.confidence >= 85 && d.status !== 'Approved').length;

    const handleBatchApprove = async () => {
        setBatchLoading(true);
        try {
            const eligible = rawRecords.filter(r =>
                (r.confidence_score?.overall_score ?? 0) >= 85 &&
                r.status !== 'auto_approved' &&
                r.status !== 'approved'
            );
            await Promise.all(
                eligible.map(r =>
                    overrideDocument(r.document_id, {
                        decision: 'approved',
                        reason: 'Batch approve ≥85%',
                        officer_name: 'Compliance Officer',
                    })
                )
            );
            await fetchDocuments();
            setShowBatchModal(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Batch approve failed');
        } finally {
            setBatchLoading(false);
        }
    };

    return (
        <div className="p-6">
            <div className="flex items-center justify-between">
                <PageHeader
                    title="Document Triage"
                    subtitle="AI-powered PPM compliance validation dashboard"
                />
                <button
                    onClick={() => navigate('/upload')}
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm font-medium"
                >
                    <Upload className="w-4 h-4" />
                    Upload / Import
                </button>
            </div>
            <StatCards stats={stats} />
            <ProcessingPipeline status={hoveredStatus ?? undefined} />
            {error && (
                <div className="mb-4 p-4 bg-destructive/10 border border-destructive/30 rounded-lg text-sm text-destructive">
                    {error}
                </div>
            )}
            {loading ? (
                <div className="flex items-center justify-center py-12 text-muted-foreground">
                    Loading documents...
                </div>
            ) : (
                <DocumentsTable
                    documents={documents}
                    onApproveAll={() => setShowBatchModal(true)}
                    onRefresh={fetchDocuments}
                    onHoverStatus={setHoveredStatus}
                />
            )}
            {showBatchModal && (
                <BatchApproveModal
                    eligibleCount={eligibleCount}
                    isLoading={batchLoading}
                    onClose={() => setShowBatchModal(false)}
                    onConfirm={handleBatchApprove}
                />
            )}
        </div>
    );
}
