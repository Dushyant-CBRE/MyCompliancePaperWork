import { FileText, ZoomIn, ZoomOut, RotateCw } from 'lucide-react';

interface PDFViewerPanelProps {
    fileName: string;
}

export function PDFViewerPanel({ fileName }: PDFViewerPanelProps) {
    return (
        <div className="flex-1 bg-muted/30 p-6 overflow-auto">
            <div className="bg-card rounded-lg border border-border p-4">
                <div className="flex items-center justify-between mb-4">
                    <h3>PDF Viewer</h3>
                    <div className="flex items-center gap-2">
                        <button className="p-2 hover:bg-muted rounded-lg transition-colors">
                            <ZoomOut className="w-4 h-4" />
                        </button>
                        <span className="px-3 py-1 bg-muted rounded text-sm">100%</span>
                        <button className="p-2 hover:bg-muted rounded-lg transition-colors">
                            <ZoomIn className="w-4 h-4" />
                        </button>
                        <button className="p-2 hover:bg-muted rounded-lg transition-colors">
                            <RotateCw className="w-4 h-4" />
                        </button>
                    </div>
                </div>
                <div className="bg-background border border-border rounded-lg aspect-[8.5/11] flex items-center justify-center">
                    <div className="text-center text-muted-foreground">
                        <FileText className="w-16 h-16 mx-auto mb-4" />
                        <p>PDF Document Preview</p>
                        <p className="text-sm mt-2">{fileName}</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
