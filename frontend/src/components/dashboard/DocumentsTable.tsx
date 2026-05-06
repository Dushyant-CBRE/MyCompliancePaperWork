import { useNavigate } from 'react-router-dom';
import { Filter, Download, ArrowUpDown, RefreshCw } from 'lucide-react';
import type { Document } from '../../types';
import { StatusBadge } from '../StatusBadge';
import { ConfidenceBar } from '../ConfidenceBar';

interface DocumentsTableProps {
    documents: Document[];
    onApproveAll: () => void;
    onRefresh: () => void;
    onHoverStatus?: (status: string | null) => void;
}

export function DocumentsTable({ documents, onApproveAll, onRefresh, onHoverStatus }: DocumentsTableProps) {
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
                                Insights
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {documents.map((doc) => (
                            <tr
                                key={doc.id}
                                onClick={() => navigate(`/document/${doc.id}`, { state: { ids } })}
                                onMouseEnter={() => onHoverStatus?.(doc.status)}
                                onMouseLeave={() => onHoverStatus?.(null)}
                                className="hover:bg-grey/40 border-l-2 border-l-transparent hover:border-l-primary transition-colors cursor-pointer group"
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
                                    <div className="flex flex-wrap gap-1.5">
                                        {doc.complianceStatus && (
                                            <span className="px-2 py-0.5 bg-red-50 text-red-700 rounded-full border border-red-200 text-xs font-medium">
                                                {doc.complianceStatus}
                                            </span>
                                        )}
                                        {doc.riskLevel && (
                                            <span className="px-2 py-0.5 bg-orange-50 text-orange-700 rounded-full border border-orange-200 text-xs font-medium">
                                                Risk: {doc.riskLevel}
                                            </span>
                                        )}
                                        {doc.remedial && (
                                            <span className="px-2 py-0.5 bg-purple-50 text-purple-700 rounded-full border border-purple-200 text-xs font-medium">
                                                Remedial Detected
                                            </span>
                                        )}
                                        {!doc.complianceStatus && !doc.riskLevel && !doc.remedial && (
                                            <span className="text-muted-foreground text-sm">—</span>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
