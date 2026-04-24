import { useState } from 'react';
import { Save } from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { ThresholdsCard } from '../components/settings/ThresholdsCard';
import { NamingConventionCard } from '../components/settings/NamingConventionCard';
import { RemedialDetectionCard } from '../components/settings/RemedialDetectionCard';
import { RoutingCard } from '../components/settings/RoutingCard';
import { RolesCard } from '../components/settings/RolesCard';

export function Settings() {
    const [autoApprove, setAutoApprove] = useState(85);
    const [manualReview, setManualReview] = useState(70);

    const handleReset = () => {
        setAutoApprove(85);
        setManualReview(70);
    };

    return (
        <div className="p-6">
            <PageHeader
                title="Settings"
                subtitle="Configure system rules, thresholds, and routing"
            />
            <div className="max-w-4xl space-y-6">
                <ThresholdsCard
                    autoApprove={autoApprove}
                    manualReview={manualReview}
                    onAutoApproveChange={setAutoApprove}
                    onManualReviewChange={setManualReview}
                />
                <NamingConventionCard />
                <RemedialDetectionCard />
                <RoutingCard />
                <RolesCard />

                <div className="flex gap-3">
                    <button className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors flex items-center gap-2 text-sm font-medium">
                        <Save className="w-4 h-4" />
                        Save Settings
                    </button>
                    <button
                        onClick={handleReset}
                        className="px-6 py-3 bg-muted rounded-lg hover:bg-muted/80 transition-colors text-sm font-medium"
                    >
                        Reset to Defaults
                    </button>
                </div>
            </div>
        </div>
    );
}
