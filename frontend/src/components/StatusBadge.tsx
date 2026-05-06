import { CheckCircle2, AlertTriangle, Clock } from 'lucide-react';
import type { DocStatus } from '../types/document-types';

function getStatusStyle(status: DocStatus) {
    switch (status) {
        case 'Auto-Approved':
            return 'bg-accent/10 text-accent border-accent/20';
        case 'Approved':
            return 'bg-green-50 text-green-700 border-green-200';
        case 'Needs Review':
            return 'bg-yellow-50 text-yellow-700 border-yellow-200';
        case 'Remedial Detected':
            return 'bg-red-50 text-red-700 border-red-200';
    }
}

interface StatusBadgeProps {
    status: DocStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
    return (
        <span
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-medium ${getStatusStyle(status)}`}
        >
            {status === 'Auto-Approved' && <CheckCircle2 className="w-3 h-3" />}
            {status === 'Approved' && <CheckCircle2 className="w-3 h-3" />}
            {status === 'Needs Review' && <Clock className="w-3 h-3" />}
            {status === 'Remedial Detected' && <AlertTriangle className="w-3 h-3" />}
            {status}
        </span>
    );
}
