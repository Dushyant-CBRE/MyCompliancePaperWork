const pipelineSteps = ['Imported', 'OCR / Extracted', 'Validated', 'Remedial Check', 'Routed'];

export function ProcessingPipeline() {
    return (
        <div className="bg-card border border-border rounded-lg p-6 mb-6">
            <h3 className="mb-4">Processing Pipeline</h3>
            <div className="flex items-center gap-2">
                {pipelineSteps.map((step, idx) => (
                    <div key={step} className="flex items-center flex-1">
                        <div className="flex-1">
                            <div className="bg-primary/10 rounded-full px-3 py-2 text-center">
                                <span className="text-sm">{step}</span>
                            </div>
                        </div>
                        {idx < pipelineSteps.length - 1 && (
                            <div className="w-4 h-0.5 bg-border flex-shrink-0" />
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
