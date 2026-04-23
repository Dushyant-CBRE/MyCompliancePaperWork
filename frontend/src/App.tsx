import './index.css';
import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom';
import { Search, Bell, ChevronDown } from 'lucide-react';
import { SideNav } from './components/SideNav';

function Header() {
    return (
        <header className="bg-card border-b border-border px-6 py-3 flex items-center justify-between shrink-0">
            {/* Search */}
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

            {/* Actions */}
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

function Layout() {
    return (
        <div className="flex h-screen bg-background">
            <SideNav />
            <div className="flex-1 flex flex-col overflow-hidden">
                <Header />
                <main className="flex-1 overflow-auto">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}

function Placeholder({ title }: { title: string }) {
    return (
        <div className="flex items-center justify-center h-full text-[var(--muted-foreground)] text-lg">
            {title} — coming soon
        </div>
    );
}

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route element={<Layout />}>
                    <Route path="/" element={<Placeholder title="Dashboard" />} />
                    <Route path="/exceptions" element={<Placeholder title="Exceptions" />} />
                    <Route path="/upload" element={<Placeholder title="Upload / Import" />} />
                    <Route path="/analytics" element={<Placeholder title="Analytics" />} />
                    <Route path="/audit" element={<Placeholder title="Audit Log" />} />
                    <Route path="/settings" element={<Placeholder title="Settings" />} />
                </Route>
            </Routes>
        </BrowserRouter>
    );
}

export default App;

