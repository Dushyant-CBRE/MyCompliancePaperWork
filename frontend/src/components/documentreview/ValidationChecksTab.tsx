import { CheckCircle2, XCircle } from 'lucide-react';
import type { ValidationCheck } from '../../types';

interface ValidationChecksTabProps {
    checks: ValidationCheck[];
}

export function ValidationChecksTab({ checks }: ValidationChecksTabProps) {
    return (
        <div className="space-y-3">
            <h3 className="mb-4">Validation Checks</h3>
            {checks.map((check, idx) => (
                <div
                    key={idx}
                    className={`flex items-start gap-3 p-4 rounded-lg ${
                        check.status === 'pass' ? 'bg-green-50' : 'bg-red-50'
                    }`}
                >
                    {check.status === 'pass' ? (
                        <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
                    ) : (
                        <XCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1">
                        <p className={check.status === 'pass' ? 'text-green-800' : 'text-red-800'}>
                            {check.check}
                        </p>
                        {check.detail && (
                            <p className="text-sm text-red-600 mt-1">{check.detail}</p>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
}
