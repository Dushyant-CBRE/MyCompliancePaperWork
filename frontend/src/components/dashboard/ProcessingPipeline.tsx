import { CheckCircle2, XCircle, Clock, Circle } from 'lucide-react';

const pipelineSteps = ['Imported', 'OCR / Extracted', 'Validated', 'Remedial Check', 'Routed'];

// Returns the state of each step index for a given document status:
// 'green' | 'red' | 'yellow' | 'default'
function getStepStates(status: string): ('green' | 'red' | 'yellow' | 'default')[] {
    const s = status.toLowerCase();
    if (s === 'approved' || s === 'auto-approved' || s === 'auto_approved') {
        return ['green', 'green', 'green', 'green', 'green'];
    }
    if (s === 'rejected') {
        return ['red', 'red', 'red', 'red', 'red'];
    }
    if (s === 'needs review' || s === 'manual_review') {
        // Up to Validated (0,1,2) green, rest yellow
        return ['green', 'green', 'green', 'yellow', 'yellow'];
    }
    if (s === 'remedial detected' || s === 'requires_attention') {
        // Up to Remedial Check (0-3) green, Routed yellow
        return ['green', 'green', 'green', 'green', 'yellow'];
    }
    return ['default', 'default', 'default', 'default', 'default'];
}

const stepStyles = {
    green:   { pill: 'bg-green-100 text-green-800 border border-green-300',   connector: 'bg-green-400',   Icon: CheckCircle2, iconCls: 'text-green-600' },
    red:     { pill: 'bg-red-100 text-red-800 border border-red-300',         connector: 'bg-red-400',     Icon: XCircle,      iconCls: 'text-red-600'   },
    yellow:  { pill: 'bg-yellow-100 text-yellow-800 border border-yellow-300',connector: 'bg-yellow-400', Icon: Clock,        iconCls: 'text-yellow-600'},
    default: { pill: 'bg-primary/10 text-foreground border border-transparent',connector: 'bg-border',     Icon: Circle,       iconCls: 'text-muted-foreground' },
};

interface ProcessingPipelineProps {
    status?: string;
}

export function ProcessingPipeline({ status }: ProcessingPipelineProps) {
    const states = status ? getStepStates(status) : Array(pipelineSteps.length).fill('default') as ('default')[];

    return (
        <div className="bg-card border border-border rounded-lg p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
                <h3>Processing Pipeline</h3>
                {status && (
                    <span className="text-xs text-muted-foreground">Showing pipeline for hovered document</span>
                )}
            </div>
            <div className="flex items-center gap-2">
                {pipelineSteps.map((step, idx) => {
                    const state = states[idx];
                    const style = stepStyles[state];
                    const { Icon } = style;
                    return (
                        <div key={step} className="flex items-center flex-1">
                            <div className="flex-1">
                                <div className={`rounded-full px-3 py-2 text-center flex items-center justify-center gap-1.5 transition-colors duration-200 ${style.pill}`}>
                                    <Icon className={`w-3.5 h-3.5 shrink-0 ${style.iconCls}`} />
                                    <span className="text-sm">{step}</span>
                                </div>
                            </div>
                            {idx < pipelineSteps.length - 1 && (
                                <div className={`w-4 h-0.5 flex-shrink-0 transition-colors duration-200 ${style.connector}`} />
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
