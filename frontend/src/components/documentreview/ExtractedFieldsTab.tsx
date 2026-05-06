import type { ExtractedField } from '../../types/review-types';

interface ExtractedFieldsTabProps {
    fields: ExtractedField[];
}

export function ExtractedFieldsTab({ fields }: ExtractedFieldsTabProps) {
    return (
        <div className="space-y-4">
            <h3 className="mb-4">Extracted Fields</h3>
            {fields.map((field, idx) => (
                <div key={idx} className="bg-muted/30 rounded-lg p-4">
                     <div className="flex items-start justify-between mb-2">
                        <span className="text-sm text-muted-foreground">{field.label}</span>
                    </div>
                    <p className="mb-2">{field.value}</p>
                    <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">{field.source}</span>
                        <div className="flex items-center gap-2">
                            <div className="w-16 bg-background rounded-full h-1.5">
                                <div
                                    className="h-full rounded-full bg-accent"
                                    style={{ width: `${field.confidence}%` }}
                                />
                            </div>
                            <span className="text-muted-foreground">{field.confidence}%</span>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}
