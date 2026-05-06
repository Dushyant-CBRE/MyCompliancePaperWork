interface SiteRow {
    site: string;
    approved: number;
    review: number;
    remedial: number;
}

interface SiteBreakdownTableProps {
    data: SiteRow[];
}

export function SiteBreakdownTable({ data }: SiteBreakdownTableProps) {
    return (
        <div className="bg-card border border-border rounded-lg p-6 mb-6">
            <h3 className="mb-4">Breakdown by Site</h3>
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead className="bg-muted/50">
                        <tr>
                            <th className="px-6 py-3 text-left text-sm font-medium">Site</th>
                            <th className="px-6 py-3 text-left text-sm font-medium">
                                Approved
                            </th>
                            <th className="px-6 py-3 text-left text-sm font-medium">
                                Needs Review
                            </th>
                            <th className="px-6 py-3 text-left text-sm font-medium">
                                Rejected
                            </th>
                            <th className="px-6 py-3 text-left text-sm font-medium">Total</th>
                            <th className="px-6 py-3 text-left text-sm font-medium">
                                Approve %
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {data.map((site) => {
                            const total = site.approved + site.review + site.remedial;
                            const approvePercent = Math.round((site.approved / total) * 100);
                            return (
                                <tr key={site.site} className="hover:bg-muted/30">
                                    <td className="px-6 py-4 text-sm">{site.site}</td>
                                    <td className="px-6 py-4">
                                        <span className="text-sm text-accent">{site.approved}</span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="text-sm text-yellow-600">
                                            {site.review}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="text-sm text-red-600">
                                            {site.remedial}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm">{total}</td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-2">
                                            <div className="flex-1 bg-muted rounded-full h-2 max-w-[100px]">
                                                <div
                                                    className="h-full rounded-full bg-accent"
                                                    style={{ width: `${approvePercent}%` }}
                                                />
                                            </div>
                                            <span className="text-sm">{approvePercent}%</span>
                                        </div>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
