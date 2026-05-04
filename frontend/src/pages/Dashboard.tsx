import { useState } from 'react';
import type { Document } from '../types/document-types';
import { PageHeader } from '../components/PageHeader';
import { StatCards } from '../components/dashboard/StatCards';
import { ProcessingPipeline } from '../components/dashboard/ProcessingPipeline';
import { DocumentsTable } from '../components/dashboard/DocumentsTable';
import { BatchApproveModal } from '../components/dashboard/BatchApproveModal';

const mockDocuments: Document[] = [
    {
        id: '1',
        site: 'DLF Cyber City',
        vendor: 'FireSafe Solutions',
        ppmType: 'Fire Safety',
        documentDate: '2026-04-15',
        uploadDate: '2026-04-20',
        status: 'Auto-Approved',
        confidence: 92,
        flags: [],
        remedial: false,
    },
    {
        id: '2',
        site: 'Udyog Vihar',
        vendor: 'ElectroTech Services',
        ppmType: 'Electrical',
        documentDate: '2026-04-18',
        uploadDate: '2026-04-21',
        status: 'Needs Review',
        confidence: 64,
        flags: ['Missing field'],
        remedial: false,
    },
    {
        id: '3',
        site: 'Golf Course Rd',
        vendor: 'ClimateControl Inc',
        ppmType: 'HVAC',
        documentDate: '2026-04-10',
        uploadDate: '2026-04-19',
        status: 'Remedial Detected',
        confidence: 87,
        flags: ['Remedial keywords'],
        remedial: true,
    },
    {
        id: '4',
        site: 'DLF Cyber City',
        vendor: 'Elevator Maintenance Co',
        ppmType: 'Elevator',
        documentDate: '2026-04-12',
        uploadDate: '2026-04-20',
        status: 'Auto-Approved',
        confidence: 95,
        flags: [],
        remedial: false,
    },
    {
        id: '5',
        site: 'Udyog Vihar',
        vendor: 'FireSafe Solutions',
        ppmType: 'Fire Safety',
        documentDate: '2026-04-08',
        uploadDate: '2026-04-18',
        status: 'Needs Review',
        confidence: 41,
        flags: ['Date mismatch', 'Wrong site'],
        remedial: false,
    },
];

const eligibleCount = mockDocuments.filter((d) => d.confidence >= 85).length;

export function Dashboard() {
    const [showBatchModal, setShowBatchModal] = useState(false);

    return (
        <div className="p-6">
            <PageHeader
                title="Document Triage"
                subtitle="AI-powered PPM compliance validation dashboard"
            />
            <StatCards />
            <ProcessingPipeline />
            <DocumentsTable
                documents={mockDocuments}
                onApproveAll={() => setShowBatchModal(true)}
            />
            {showBatchModal && (
                <BatchApproveModal
                    eligibleCount={eligibleCount}
                    onClose={() => setShowBatchModal(false)}
                    onConfirm={() => setShowBatchModal(false)}
                />
            )}
        </div>
    );
}
