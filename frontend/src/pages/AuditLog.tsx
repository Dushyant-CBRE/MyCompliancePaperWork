import { useState, useEffect } from 'react';
import type { AuditEntry } from '../types/audit-types';
import { PageHeader } from '../components/PageHeader';
import { AuditToolbar } from '../components/auditlog/AuditToolbar';
import { AuditTable } from '../components/auditlog/AuditTable';
import { fetchAuditLog } from '../api/audit-api';

export function AuditLog() {
    const [entries, setEntries] = useState<AuditEntry[]>([]);
    const [total, setTotal] = useState(0);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        setIsLoading(true);
        fetchAuditLog({ limit: 100 })
            .then((result) => {
                setEntries(result.entries);
                setTotal(result.total);
            })
            .catch((err) => {
                setError(err instanceof Error ? err.message : 'Failed to load audit log');
            })
            .finally(() => setIsLoading(false));
    }, []);

    return (
        <div className="p-6">
            <PageHeader
                title="Audit Log"
                subtitle="Complete decision history and action tracking"
            />
            <div className="bg-card border border-border rounded-lg">
                <AuditToolbar />
                {isLoading ? (
                    <div className="p-12 text-center text-muted-foreground text-sm">
                        Loading audit log...
                    </div>
                ) : error ? (
                    <div className="p-12 text-center text-destructive text-sm">
                        {error}
                    </div>
                ) : entries.length === 0 ? (
                    <div className="p-12 text-center text-muted-foreground text-sm">
                        No audit entries found.
                    </div>
                ) : (
                    <AuditTable entries={entries} />
                )}
                <div className="p-4 border-t border-border flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">
                        Showing {entries.length} of {total} entries
                    </p>
                </div>
            </div>
        </div>
    );
}
