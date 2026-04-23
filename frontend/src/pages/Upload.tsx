import { useState } from 'react';
import { PIPELINE_STAGES } from '../lib/constants';
import type { Stage } from '../lib/constants';
import { PageHeader } from '../components/PageHeader';
import { DropZone } from '../components/upload/DropZone';
import { UploadPipelineCard } from '../components/upload/UploadPipelineCard';
import { MetadataForm } from '../components/upload/MetadataForm';

export function Upload() {
    const [uploadProgress, setUploadProgress] = useState<Stage | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [isDragOver, setIsDragOver] = useState(false);

    const simulateUpload = () => {
        setIsProcessing(true);
        let currentIndex = 0;

        const interval = setInterval(() => {
            if (currentIndex < PIPELINE_STAGES.length) {
                setUploadProgress(PIPELINE_STAGES[currentIndex]);
                currentIndex++;
            } else {
                clearInterval(interval);
                setTimeout(() => {
                    setIsProcessing(false);
                    setUploadProgress(null);
                }, 1000);
            }
        }, 800);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(false);
        simulateUpload();
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(true);
    };

    const handleDragLeave = () => setIsDragOver(false);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            simulateUpload();
        }
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
                {isProcessing && <UploadPipelineCard currentStage={uploadProgress} />}
                <MetadataForm />
            </div>
        </div>
    );
}
