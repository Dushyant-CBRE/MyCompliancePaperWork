import { Clock, TrendingUp, CheckCircle, AlertCircle } from 'lucide-react';

interface AnalyticsStatCardsProps {
    autoApproveRate: number;
    criticalAlerts: number;
    overrideRate: number;
    avgProcessingTime: string;
}

export function AnalyticsStatCards({ autoApproveRate, criticalAlerts, overrideRate, avgProcessingTime }: AnalyticsStatCardsProps) {
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
                    <p className="text-sm text-muted-foreground">Auto-Approve Rate</p>
                    <TrendingUp className="w-4 h-4 text-accent" />
                </div>
                <p className="mb-1">{autoApproveRate.toFixed(1)}%</p>
                <p className="text-sm text-accent">Live from backend</p>
            </div>

            <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-muted-foreground">Override Rate</p>
                    <CheckCircle className="w-4 h-4 text-muted-foreground" />
                </div>
                <p className="mb-1">{overrideRate.toFixed(1)}%</p>
                <p className="text-sm text-muted-foreground">Within acceptable range</p>
            </div>

            <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-muted-foreground">Critical Alerts</p>
                    <AlertCircle className="w-4 h-4 text-red-500" />
                </div>
                <p className="mb-1">{criticalAlerts}</p>
                <p className="text-sm text-red-600">Requires attention</p>
            </div>
        </div>
    );
}
