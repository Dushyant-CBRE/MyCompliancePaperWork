import { Clock, TrendingUp, CheckCircle, AlertCircle } from 'lucide-react';

interface AnalyticsStatCardsProps {
    approveRate: number;
    needsReviewCount: number;
    rejectedRate: number;
    avgProcessingTime: string;
}

export function AnalyticsStatCards({ approveRate, needsReviewCount, rejectedRate, avgProcessingTime }: AnalyticsStatCardsProps) {
    return (
        <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-muted-foreground">Avg Processing Time</p>
                    <Clock className="w-4 h-4 text-accent" />
                </div>
                <p className="mb-1">{avgProcessingTime}</p>
                <p className="text-sm text-accent">Target: &lt;2 minutes</p>
            </div>

            <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-muted-foreground">Approve Rate</p>
                    <TrendingUp className="w-4 h-4 text-accent" />
                </div>
                <p className="mb-1">{approveRate.toFixed(1)}%</p>
                <p className="text-sm text-accent">Live from backend</p>
            </div>

            <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-muted-foreground">Rejected Rate</p>
                    <CheckCircle className="w-4 h-4 text-muted-foreground" />
                </div>
                <p className="mb-1">{rejectedRate.toFixed(1)}%</p>
                <p className="text-sm text-muted-foreground">Within acceptable range</p>
            </div>

            <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-muted-foreground">Needs Review</p>
                    <AlertCircle className="w-4 h-4 text-yellow-500" />
                </div>
                <p className="mb-1">{needsReviewCount}</p>
                <p className="text-sm text-yellow-600">Pending review</p>
            </div>
        </div>
    );
}
