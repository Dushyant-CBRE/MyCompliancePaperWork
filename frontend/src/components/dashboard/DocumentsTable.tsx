import { useNavigate } from 'react-router-dom';
import { Filter, Download, ArrowUpDown, RefreshCw } from 'lucide-react';
import type { Document } from '../../types';
import { StatusBadge } from '../StatusBadge';
import { ConfidenceBar } from '../ConfidenceBar';

interface DocumentsTableProps {
    documents: Document[];
    onApproveAll: () => void;
    onRefresh: () => void;
}

export function DocumentsTable({ documents, onApproveAll, onRefresh }: DocumentsTableProps) {
    const navigate = useNavigate();
    const ids = documents.map((d) => d.id);
    return (
        <div className="bg-card border border-border rounded-lg">
            {/* Toolbar */}
            <div className="p-6 border-b border-border">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <button className="px-4 py-2 bg-muted rounded-lg hover:bg-muted/80 transition-colors flex items-center gap-2 text-sm">
                            <Filter className="w-4 h-4" />
                            Filters
                        </button>
                        <button className="px-4 py-2 bg-muted rounded-lg hover:bg-muted/80 transition-colors flex items-center gap-2 text-sm">
                            <ArrowUpDown className="w-4 h-4" />
                            Sort
                        </button>
                        <button
                            onClick={onRefresh}
                            className="px-4 py-2 bg-muted rounded-lg hover:bg-muted/80 transition-colors flex items-center gap-2 text-sm"
                        >
                            <RefreshCw className="w-4 h-4" />
                            Refresh
                        </button>
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={onApproveAll}
                            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm font-medium"
                        >
                            Approve All ≥85%
                        </button>
                        <button className="px-4 py-2 bg-muted rounded-lg hover:bg-muted/80 transition-colors flex items-center gap-2 text-sm">
                            <Download className="w-4 h-4" />
                            Export
                        </button>
                    </div>
                </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead className="bg-muted/50">
                        <tr>
                            <th className="px-6 py-3 text-left text-sm font-medium text-muted-foreground">
                                Site / Facility
                            </th>
                            <th className="px-6 py-3 text-left text-sm font-medium text-muted-foreground">
                                Vendor
                            </th>
                            <th className="px-6 py-3 text-left text-sm font-medium text-muted-foreground">
                                PPM Type
                            </th>
                            <th className="px-6 py-3 text-left text-sm font-medium text-muted-foreground">
                                Document Date
                            </th>
                            <th className="px-6 py-3 text-left text-sm font-medium text-muted-foreground">
                                Status
                            </th>
                            <th className="px-6 py-3 text-left text-sm font-medium text-muted-foreground">
                                Confidence
                            </th>
                            <th className="px-6 py-3 text-left text-sm font-medium text-muted-foreground">
                                Flags
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {documents.map((doc) => (
                            <tr
                                key={doc.id}
                                onClick={() => navigate(`/document/${doc.id}`, { state: { ids } })}
                                className="hover:bg-muted/30 transition-colors cursor-pointer"
                            >
                                <td className="px-6 py-4 text-sm font-medium">
                                    {doc.site}
                                </td>
                                <td className="px-6 py-4 text-sm">{doc.vendor}</td>
                                <td className="px-6 py-4 text-sm">{doc.ppmType}</td>
                                <td className="px-6 py-4 text-sm">{doc.documentDate}</td>
                                <td className="px-6 py-4">
                                    <StatusBadge status={doc.status} />
                                </td>
                                <td className="px-6 py-4">
                                    <ConfidenceBar confidence={doc.confidence} />
                                </td>
                                <td className="px-6 py-4">
                                    {doc.flags.length > 0 ? (
                                        <div className="flex flex-wrap gap-1">
                                            {doc.flags.map((flag) => (
                                                <span
                                                    key={flag}
                                                    className="px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded text-xs"
                                                >
                                                    {flag}
                                                </span>
                                            ))}
                                        </div>
                                    ) : (
                                        <span className="text-muted-foreground text-sm">None</span>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
