import { Search, Bell, ChevronDown } from 'lucide-react';

export function Header() {
    return (
        <header className="bg-card border-b border-border px-6 py-3 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-4 flex-1 max-w-xl">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="Search documents, sites, vendors..."
                        className="w-full pl-10 pr-4 py-2 bg-input-background rounded-lg text-sm border-0 outline-none focus:ring-2 focus:ring-ring"
                    />
                </div>
            </div>

            <div className="flex items-center gap-3">
                <button className="relative p-2 hover:bg-muted rounded-lg transition-colors">
                    <Bell className="w-5 h-5" />
                    <span className="absolute top-1 right-1 w-2 h-2 bg-destructive rounded-full" />
                </button>

                <div className="flex items-center gap-2 px-3 py-2 hover:bg-muted rounded-lg cursor-pointer transition-colors">
                    <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-semibold">
                        CO
                    </div>
                    <span className="text-sm font-medium">Compliance Officer</span>
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                </div>
            </div>
        </header>
    );
}
