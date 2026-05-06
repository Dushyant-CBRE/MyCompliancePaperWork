import { useState } from 'react';
import { FileText, ZoomIn, ZoomOut, RotateCw, Download, Maximize2 } from 'lucide-react';

interface PDFViewerPanelProps {
    fileName: string;
    blobUrl?: string | null;
    pdfLoading?: boolean;
}

const ZOOM_LEVELS = [50, 75, 100, 125, 150, 200];

export function PDFViewerPanel({ fileName, blobUrl, pdfLoading }: PDFViewerPanelProps) {
    const [zoomIndex, setZoomIndex] = useState(2); // default 100%
    const [rotation, setRotation] = useState(0);   // 0, 90, 180, 270

    const zoom = ZOOM_LEVELS[zoomIndex];

    const zoomOut = () => setZoomIndex((i) => Math.max(0, i - 1));
    const zoomIn = () => setZoomIndex((i) => Math.min(ZOOM_LEVELS.length - 1, i + 1));
    const rotate = () => setRotation((r) => (r + 90) % 360);

    // Appending #zoom= triggers the browser PDF plugin to apply zoom on load.
    // Using a key forces iframe remount when zoom changes.
    const iframeSrc = blobUrl ? `${blobUrl}#zoom=${zoom}&toolbar=1` : null;

    return (
        <div className="flex-1 bg-muted/30 p-6 overflow-auto flex flex-col gap-4">
            <div className="bg-card rounded-lg border border-border p-4 flex flex-col flex-1">
                {/* Toolbar */}
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2 text-sm font-medium truncate max-w-xs">
                        <FileText className="w-4 h-4 text-muted-foreground shrink-0" />
                        <span className="truncate text-muted-foreground">{fileName}</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <button
                            onClick={zoomOut}
                            disabled={zoomIndex === 0}
                            title="Zoom out"
                            className="p-2 hover:bg-muted rounded-lg transition-colors disabled:opacity-40"
                        >
                            <ZoomOut className="w-4 h-4" />
                        </button>
                        <span className="px-3 py-1 bg-muted rounded text-sm min-w-[56px] text-center">
                            {zoom}%
                        </span>
                        <button
                            onClick={zoomIn}
                            disabled={zoomIndex === ZOOM_LEVELS.length - 1}
                            title="Zoom in"
                            className="p-2 hover:bg-muted rounded-lg transition-colors disabled:opacity-40"
                        >
                            <ZoomIn className="w-4 h-4" />
                        </button>
                        <div className="w-px h-5 bg-border mx-1" />
                        <button
                            onClick={rotate}
                            title="Rotate 90°"
                            className="p-2 hover:bg-muted rounded-lg transition-colors"
                        >
                            <RotateCw className="w-4 h-4" />
                        </button>
                        {blobUrl && (
                            <>
                                <div className="w-px h-5 bg-border mx-1" />
                                <a
                                    href={blobUrl}
                                    download={fileName}
                                    title="Download"
                                    className="p-2 hover:bg-muted rounded-lg transition-colors"
                                >
                                    <Download className="w-4 h-4" />
                                </a>
                                <a
                                    href={blobUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    title="Open in new tab"
                                    className="p-2 hover:bg-muted rounded-lg transition-colors"
                                >
                                    <Maximize2 className="w-4 h-4" />
                                </a>
                            </>
                        )}
                    </div>
                </div>

                {/* PDF area */}
                <div className="flex-1 bg-background border border-border rounded-lg overflow-hidden flex items-center justify-center min-h-[500px]">
                    {pdfLoading ? (
                        <div className="text-center text-muted-foreground">
                            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                            <p className="text-sm">Loading PDF…</p>
                        </div>
                    ) : iframeSrc ? (
                        <div
                            className="w-full h-full transition-transform duration-200 origin-center"
                            style={{ transform: `rotate(${rotation}deg)` }}
                        >
                            <iframe
                                key={`${iframeSrc}-${zoom}`}
                                src={iframeSrc}
                                title={fileName}
                                className="w-full h-full border-0"
                            />
                        </div>
                    ) : (
                        <div className="text-center text-muted-foreground">
                            <FileText className="w-16 h-16 mx-auto mb-4 opacity-40" />
                            <p className="font-medium">No PDF available</p>
                            <p className="text-sm mt-2">{fileName}</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
