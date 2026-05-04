import { Link } from 'react-router-dom';
import { AlertTriangle, Clock, User } from 'lucide-react';
import type { Exception, Severity } from '../../types/exception-types';
import { ConfidenceBar } from '../ConfidenceBar';

function getSeverityStyle(severity: Severity) {
    switch (severity) {
        case 'Critical':
            return 'bg-red-100 text-red-800 border-red-200';
        case 'High':
            return 'bg-orange-100 text-orange-800 border-orange-200';
        case 'Medium':
            return 'bg-yellow-100 text-yellow-800 border-yellow-200';
        default:
            return 'bg-muted text-muted-foreground border-border';
    }
}

interface ExceptionCardProps {
    exception: Exception;
}

export function ExceptionCard({ exception }: ExceptionCardProps) {
    const isCritical = exception.severity === 'Critical';

    return (
        <div
            className={`bg-card border-2 rounded-lg p-6 ${isCritical ? 'border-red-300' : 'border-border'}`}
        >
            {isCritical && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 flex items-center gap-3">
                    <AlertTriangle className="w-5 h-5 text-red-700 flex-shrink-0" />
                    <div className="flex-1">
                        <p className="text-red-900 text-sm font-medium">
                            Immediate Attention Required
                        </p>
                        <p className="text-sm text-red-700 mt-0.5">
                            Critical remedial actions detected
                        </p>
                    </div>
                </div>
            )}

            <div className="flex items-start justify-between">
                {/* Left: details */}
                <div className="flex-1">
                    <div className="flex items-center gap-3 mb-4">
                        <Link
                            to={`/document/${exception.id}`}
                            className="hover:text-primary transition-colors font-medium"
                        >
                            {exception.site}
                        </Link>
                        <span
                            className={`px-3 py-1 rounded-full border text-xs font-medium ${getSeverityStyle(exception.severity)}`}
                        >
                            {exception.severity}
                        </span>
                    </div>

                    <div className="grid grid-cols-4 gap-4">
                        <div>
                            <p className="text-sm text-muted-foreground">Vendor</p>
                            <p className="mt-1 text-sm">{exception.vendor}</p>
                        </div>
                        <div>
                            <p className="text-sm text-muted-foreground">PPM Type</p>
                            <p className="mt-1 text-sm">{exception.ppmType}</p>
                        </div>
                        <div>
                            <p className="text-sm text-muted-foreground">Reason</p>
                            <p className="mt-1 text-sm">{exception.reason}</p>
                        </div>
                        <div>
                            <p className="text-sm text-muted-foreground">Confidence</p>
                            <div className="mt-1">
                                <ConfidenceBar confidence={exception.confidence} />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right: SLA + actions */}
                <div className="ml-6 flex flex-col items-end gap-3 flex-shrink-0">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Clock className="w-4 h-4" />
                        <span>SLA: {exception.sla}</span>
                    </div>

                    {exception.assignee ? (
                        <div className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded-lg text-sm">
                            <User className="w-4 h-4" />
                            <span>{exception.assignee}</span>
                        </div>
                    ) : (
                        <button className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm font-medium">
                            Assign to Me
                        </button>
                    )}

                    <Link
                        to={`/document/${exception.id}`}
                        className="px-4 py-2 bg-muted rounded-lg hover:bg-muted/80 transition-colors text-sm"
                    >
                        Review Document
                    </Link>
                </div>
            </div>
        </div>
    );
}
