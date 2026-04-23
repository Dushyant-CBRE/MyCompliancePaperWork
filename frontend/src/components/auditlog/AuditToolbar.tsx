import { Search, Filter, Download } from 'lucide-react';

export function AuditToolbar() {
    return (
        <div className="p-6 border-b border-border">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1 max-w-xl">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <input
                            type="text"
                            placeholder="Search by document, user, or action..."
                            className="w-full pl-10 pr-4 py-2 bg-input-background rounded-lg border-0 focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                        />
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <button className="px-4 py-2 bg-muted rounded-lg hover:bg-muted/80 transition-colors flex items-center gap-2 text-sm">
                        <Filter className="w-4 h-4" />
                        Filters
                    </button>
                    <button className="px-4 py-2 bg-muted rounded-lg hover:bg-muted/80 transition-colors flex items-center gap-2 text-sm">
                        <Download className="w-4 h-4" />
                        Export
                    </button>
                </div>
            </div>
        </div>
    );
}
