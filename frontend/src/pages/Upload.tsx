import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PIPELINE_STAGES } from '../lib/constants';
import type { Stage } from '../lib/constants';
import { PageHeader } from '../components/PageHeader';
import { DropZone } from '../components/upload/DropZone';
import { UploadPipelineCard } from '../components/upload/UploadPipelineCard';
import { MetadataForm } from '../components/upload/MetadataForm';
import type { MetadataValues } from '../components/upload/MetadataForm';
import { uploadDocument } from '../api/upload-api';

export function Upload() {
    const navigate = useNavigate();
    const [uploadProgress, setUploadProgress] = useState<Stage | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [isDragOver, setIsDragOver] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [documentId, setDocumentId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [metadata, setMetadata] = useState<MetadataValues>({
        expected_site_name: '',
        expected_ppm_type: '',
        expected_document_date: '',
        expected_vendor_name: '',
        smartsheet: false,
    });

    const handleUpload = async (file: File) => {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            setError('Only PDF files are supported.');
            return;
        }

        setSelectedFile(file);
        setIsProcessing(true);
        setError(null);
        setDocumentId(null);

        // Animate through stages while the API processes synchronously (~5-15s)
        let idx = 0;
        setUploadProgress(PIPELINE_STAGES[0]);
        const stageTimer = setInterval(() => {
            idx++;
            if (idx < PIPELINE_STAGES.length - 1) {
                setUploadProgress(PIPELINE_STAGES[idx]);
            } else {
                clearInterval(stageTimer);
            }
        }, 3000);

        const notes = [
            metadata.smartsheet ? 'Imported from Smartsheet' : '',
        ].filter(Boolean).join('; ') || undefined;

        try {
            const result = await uploadDocument(file, {
                expected_site_name: metadata.expected_site_name || undefined,
                expected_ppm_type: metadata.expected_ppm_type || undefined,
                expected_document_date: metadata.expected_document_date || undefined,
                expected_document_type: file.name.split('.')[1] || undefined,
                expected_vendor_name: metadata.expected_vendor_name || undefined,
                notes,
            });
            clearInterval(stageTimer);
            setUploadProgress('Completed');
            setDocumentId(result.document_id);
        } catch (err) {
            clearInterval(stageTimer);
            setIsProcessing(false);
            setUploadProgress(null);
            setError(err instanceof Error ? err.message : 'Upload failed. Please try again.');
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file) handleUpload(file);
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(true);
    };

    const handleDragLeave = () => setIsDragOver(false);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) handleUpload(file);
    };

    return (
        <div className="p-6">
            <PageHeader title="Upload / Import" subtitle="Upload PPM documents for AI processing" />
            <div className="w-full">
                <DropZone
                    isDragOver={isDragOver}
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onFileSelect={handleFileSelect}
                />
                {error && (
                    <div className="mt-4 p-4 bg-destructive/10 border border-destructive/30 rounded-lg text-sm text-destructive">
                        {error}
                    </div>
                )}
                {isProcessing && selectedFile && (
                    <UploadPipelineCard
                        currentStage={uploadProgress}
                        filename={selectedFile.name}
                        fileSize={`${(selectedFile.size / 1024 / 1024).toFixed(1)} MB`}
                        onOpenReview={() => navigate(`/document/${documentId}`)}
                    />
                )}
                <MetadataForm values={metadata} onChange={setMetadata} />
            </div>
        </div>
    );
}
