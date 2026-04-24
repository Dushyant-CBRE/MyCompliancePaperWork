import type { AuditEntry } from '../../types';

interface AuditTableProps {
    entries: AuditEntry[];
}

function getActionColor(action: string): string {
    switch (action) {
        case 'Auto-Approved':
        case 'Batch Approve':
            return 'bg-green-50 text-green-800 border-green-200';
        case 'Override':
            return 'bg-yellow-50 text-yellow-800 border-yellow-200';
        case 'Reject':
            return 'bg-red-50 text-red-800 border-red-200';
        case 'Remedial Detected':
            return 'bg-orange-50 text-orange-800 border-orange-200';
        default:
            return 'bg-muted text-muted-foreground border-border';
    }
}

function getInitials(name: string): string {
    return name
        .split(' ')
        .map((n) => n[0])
        .join('');
}

export function AuditTable({ entries }: AuditTableProps) {
    return (
        <div className="overflow-x-auto">
            <table className="w-full">
                <thead className="bg-muted/50">
                    <tr>
                        <th className="px-6 py-3 text-left text-sm font-medium">Timestamp</th>
                        <th className="px-6 py-3 text-left text-sm font-medium">User</th>
                        <th className="px-6 py-3 text-left text-sm font-medium">Action</th>
                        <th className="px-6 py-3 text-left text-sm font-medium">Document</th>
                        <th className="px-6 py-3 text-left text-sm font-medium">Details</th>
                        <th className="px-6 py-3 text-left text-sm font-medium">Training</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-border">
                    {entries.map((entry) => {
                        const [date, time] = entry.timestamp.split(' ');
                        return (
                            <tr key={entry.id} className="hover:bg-muted/30">
                                <td className="px-6 py-4">
                                    <div className="text-sm">
                                        <div>{date}</div>
                                        <div className="text-muted-foreground">{time}</div>
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-2">
                                        <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-medium shrink-0">
                                            {getInitials(entry.user)}
                                        </div>
                                        <span className="text-sm">{entry.user}</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <span
                                        className={`inline-flex px-3 py-1 rounded-full border text-sm ${getActionColor(entry.action)}`}
                                    >
                                        {entry.action}
                                    </span>
                                </td>
                                <td className="px-6 py-4">
                                    <p className="text-sm max-w-xs truncate">{entry.document}</p>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="max-w-md">
                                        <p className="text-sm">{entry.details}</p>
                                        {entry.reason && (
                                            <p className="text-sm text-muted-foreground mt-1">
                                                Reason: {entry.reason}
                                            </p>
                                        )}
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    {entry.trainingFeedback && (
                                        <span className="inline-flex px-2 py-1 bg-blue-50 text-blue-800 rounded text-xs">
                                            Training
                                        </span>
                                    )}
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}
