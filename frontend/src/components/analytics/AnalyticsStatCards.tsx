import { Clock, TrendingUp, CheckCircle, AlertCircle } from 'lucide-react';

export function AnalyticsStatCards() {
    return (
        <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-muted-foreground">Avg Processing Time</p>
                    <Clock className="w-4 h-4 text-accent" />
                </div>
                <p className="mb-1">1m 47s</p>
                <p className="text-sm text-accent">Target: &lt;2 minutes</p>
            </div>

            <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-muted-foreground">Auto-Approve Rate</p>
                    <TrendingUp className="w-4 h-4 text-accent" />
                </div>
                <p className="mb-1">75%</p>
                <p className="text-sm text-accent">+5% vs last week</p>
            </div>

            <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-muted-foreground">Override Rate</p>
                    <CheckCircle className="w-4 h-4 text-muted-foreground" />
                </div>
                <p className="mb-1">8.2%</p>
                <p className="text-sm text-muted-foreground">Within acceptable range</p>
            </div>

            <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-muted-foreground">Critical Alerts</p>
                    <AlertCircle className="w-4 h-4 text-red-500" />
                </div>
                <p className="mb-1">2</p>
                <p className="text-sm text-red-600">Requires attention</p>
            </div>
        </div>
    );
}
