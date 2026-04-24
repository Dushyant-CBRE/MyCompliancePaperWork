import { Upload as UploadIcon } from 'lucide-react';

interface DropZoneProps {
    isDragOver: boolean;
    onDrop: (e: React.DragEvent) => void;
    onDragOver: (e: React.DragEvent) => void;
    onDragLeave: () => void;
    onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export function DropZone({ isDragOver, onDrop, onDragOver, onDragLeave, onFileSelect }: DropZoneProps) {
    return (
        <div
            onDrop={onDrop}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer ${
                isDragOver
                    ? 'border-primary bg-muted/30'
                    : 'border-border hover:border-primary hover:bg-muted/30'
            }`}
        >
            <UploadIcon className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="mb-2">Drag and drop files here</h3>
            <p className="text-muted-foreground mb-6">
                Supports PDF, images (JPG, PNG), and Word documents
            </p>
            <label className="inline-block px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors cursor-pointer text-sm font-medium">
                Browse Files
                <input
                    type="file"
                    multiple
                    accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                    onChange={onFileSelect}
                    className="hidden"
                />
            </label>
        </div>
    );
}
