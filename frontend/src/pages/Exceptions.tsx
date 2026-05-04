import type { Exception } from '../types/exception-types';
import { PageHeader } from '../components/PageHeader';
import { ExceptionStatCards } from '../components/exceptions/ExceptionStatCards';
import { ExceptionCard } from '../components/exceptions/ExceptionCard';

const mockExceptions: Exception[] = [
    {
        id: '3',
        site: 'Golf Course Rd',
        vendor: 'ClimateControl Inc',
        ppmType: 'HVAC',
        severity: 'Critical',
        reason: 'Remedial action detected',
        confidence: 87,
        sla: '2h 15m',
        assignee: null,
    },
    {
        id: '2',
        site: 'Udyog Vihar',
        vendor: 'ElectroTech Services',
        ppmType: 'Electrical',
        severity: 'Medium',
        reason: 'Low confidence (64%)',
        confidence: 64,
        sla: '5h 42m',
        assignee: 'Priya Sharma',
    },
    {
        id: '5',
        site: 'Udyog Vihar',
        vendor: 'FireSafe Solutions',
        ppmType: 'Fire Safety',
        severity: 'High',
        reason: 'Multiple validation failures',
        confidence: 41,
        sla: '1h 08m',
        assignee: null,
    },
];

export function Exceptions() {
    return (
        <div className="p-6">
            <PageHeader
                title="Exceptions Queue"
                subtitle="Documents requiring immediate attention"
            />
            <ExceptionStatCards />
            <div className="space-y-4">
                {mockExceptions.map((exception) => (
                    <ExceptionCard key={exception.id} exception={exception} />
                ))}
            </div>
        </div>
    );
}
