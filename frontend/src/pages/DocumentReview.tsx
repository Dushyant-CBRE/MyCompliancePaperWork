import { useState } from 'react';
import { useParams } from 'react-router-dom';
import type { ReviewDocument, ExtractedField, ValidationCheck, RemedialEvidence } from '../types/review-types';
import { DocumentReviewHeader } from '../components/documentreview/DocumentReviewHeader';
import { PDFViewerPanel } from '../components/documentreview/PDFViewerPanel';
import { AnalysisPanel } from '../components/documentreview/AnalysisPanel';
import { OverrideModal } from '../components/documentreview/OverrideModal';

type TabId = 'fields' | 'validation' | 'remedial' | 'audit';

const mockDoc: ReviewDocument = {
    name: 'Fire_Safety_PPM_DLF_Cyber_City_2026-04-15.pdf',
    site: 'DLF Cyber City',
    ppmType: 'Fire Safety',
    confidence: 87,
    aiDecision: 'Remedial Detected',
    riskLevel: 'High',
    slaRemaining: '4h 23m',
};

const mockFields: ExtractedField[] = [
    { label: 'Site Name', value: 'DLF Cyber City', confidence: 98, source: 'Page 1, Header' },
    {
        label: 'PPM Type',
        value: 'Fire Safety Inspection',
        confidence: 95,
        source: 'Page 1, Title',
    },
    { label: 'Document Date', value: '2026-04-15', confidence: 92, source: 'Page 1, Date field' },
    {
        label: 'Vendor Name',
        value: 'FireSafe Solutions Pvt Ltd',
        confidence: 97,
        source: 'Page 1, Footer',
    },
    { label: 'Inspector Name', value: 'Rajesh Kumar', confidence: 89, source: 'Page 2, Signature' },
    {
        label: 'Certificate Number',
        value: 'FS-2026-041-DLF',
        confidence: 94,
        source: 'Page 1, Header',
    },
];

const mockChecks: ValidationCheck[] = [
    { check: 'Site matches facility database', status: 'pass' },
    { check: 'PPM type is valid', status: 'pass' },
    { check: 'Document date within acceptable range', status: 'pass' },
    { check: 'Naming convention follows standard', status: 'pass' },
    {
        check: 'All required fields present',
        status: 'fail',
        detail: 'Emergency contact missing',
    },
];

const mockEvidence: RemedialEvidence[] = [
    {
        text: 'Fire extinguisher refill required by 2026-05-01',
        page: 3,
        severity: 'High',
    },
    {
        text: 'Emergency exit door mechanism needs repair',
        page: 4,
        severity: 'Medium',
    },
];

export function DocumentReview() {
    const { id } = useParams();
    const [activeTab, setActiveTab] = useState<TabId>('fields');
    const [showOverrideModal, setShowOverrideModal] = useState(false);

    return (
        <div className="h-full flex flex-col">
            <DocumentReviewHeader
                doc={mockDoc}
                id={id}
                onOverride={() => setShowOverrideModal(true)}
            />

            <div className="flex-1 flex overflow-hidden">
                <PDFViewerPanel fileName={mockDoc.name} />
                <AnalysisPanel
                    activeTab={activeTab}
                    onTabChange={setActiveTab}
                    fields={mockFields}
                    checks={mockChecks}
                    evidence={mockEvidence}
                />
            </div>

            {showOverrideModal && (
                <OverrideModal onClose={() => setShowOverrideModal(false)} />
            )}
        </div>
    );
}
