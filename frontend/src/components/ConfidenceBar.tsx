function getBarColor(confidence: number) {
    if (confidence >= 85) return 'bg-accent';
    if (confidence >= 70) return 'bg-yellow-400';
    return 'bg-red-400';
}

interface ConfidenceBarProps {
    confidence: number;
}

export function ConfidenceBar({ confidence }: ConfidenceBarProps) {
    return (
        <div className="flex items-center gap-2">
            <div className="w-20 bg-muted rounded-full h-2">
                <div
                    className={`h-full rounded-full ${getBarColor(confidence)}`}
                    style={{ width: `${confidence}%` }}
                />
            </div>
            <span className="text-sm tabular-nums">{confidence}%</span>
        </div>
    );
}
