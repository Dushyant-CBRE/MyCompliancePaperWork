import { ArrowLeft, Bell, ChevronDown } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';

export function Header() {
    const location = useLocation();
    const navigate = useNavigate();
    const isDocumentReview = location.pathname.startsWith('/document/');

    return (
        <header className="bg-card border-b border-border px-6 py-3 flex items-center justify-between shrink-0">

            <div className="flex items-center gap-2">
                {isDocumentReview && (
                    <button
                        onClick={() => navigate('/')}
                        className="flex items-center gap-1.5 p-2 hover:bg-muted rounded-lg transition-colors text-sm font-medium"
                        title="Back to dashboard"
                    >
                        <ArrowLeft className="w-5 h-5" />
                        Back
                    </button>
                )}
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
