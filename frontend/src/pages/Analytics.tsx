import { PageHeader } from '../components/PageHeader';
import { AnalyticsStatCards } from '../components/analytics/AnalyticsStatCards';
import { ProcessingLineChart } from '../components/analytics/ProcessingLineChart';
import { ConfidenceBarChart } from '../components/analytics/ConfidenceBarChart';
import { SiteBreakdownTable } from '../components/analytics/SiteBreakdownTable';
import { QualitySafetyCard } from '../components/analytics/QualitySafetyCard';
import { PPMDistributionCard } from '../components/analytics/PPMDistributionCard';

const processingData = [
    { time: '00:00', count: 12 },
    { time: '04:00', count: 8 },
    { time: '08:00', count: 24 },
    { time: '12:00', count: 32 },
    { time: '16:00', count: 28 },
    { time: '20:00', count: 15 },
];

const confidenceDistribution = [
    { range: '0-20', count: 2 },
    { range: '20-40', count: 5 },
    { range: '40-60', count: 12 },
    { range: '60-80', count: 38 },
    { range: '80-100', count: 191 },
];

const siteBreakdown = [
    { site: 'DLF Cyber City', approved: 78, review: 12, remedial: 3 },
    { site: 'Udyog Vihar', approved: 64, review: 18, remedial: 4 },
    { site: 'Golf Course Rd', approved: 44, review: 12, remedial: 1 },
];

export function Analytics() {
    return (
        <div className="p-6">
            <PageHeader
                title="Analytics & Accuracy"
                subtitle="System performance and quality metrics"
            />
            <AnalyticsStatCards />
            <div className="grid grid-cols-2 gap-6 mb-6">
                <ProcessingLineChart data={processingData} />
                <ConfidenceBarChart data={confidenceDistribution} />
            </div>
            <div className="mb-6">
                <SiteBreakdownTable data={siteBreakdown} />
            </div>
            <div className="grid grid-cols-2 gap-6">
                <QualitySafetyCard />
                <PPMDistributionCard />
            </div>
        </div>
    );
}
