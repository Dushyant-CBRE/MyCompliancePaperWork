import { NavLink } from 'react-router-dom';
import {
    LayoutDashboard,
    AlertTriangle,
    Upload,
    BarChart3,
    FileSearch,
    Settings,
} from 'lucide-react';

const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/exceptions', label: 'Exceptions', icon: AlertTriangle },
    { to: '/upload', label: 'Upload/Import', icon: Upload },
    { to: '/analytics', label: 'Analytics', icon: BarChart3 },
    { to: '/audit', label: 'Audit Log', icon: FileSearch },
    { to: '/settings', label: 'Settings', icon: Settings },
];

export function SideNav() {
    return (
        <aside className="w-64 bg-sidebar text-sidebar-foreground flex flex-col h-screen flex-shrink-0">
            {/* Logo / Brand */}
            <div className="p-6 border-b border-sidebar-border">
                <h1 className="text-2xl font-bold text-white leading-tight">CBRE</h1>
                <p className="text-xs text-sidebar-foreground/70 mt-1 tracking-wide">Compliance Paperwork</p>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4">
                {navItems.map(({ to, label, icon: Icon }) => (
                    <NavLink
                        key={to}
                        to={to}
                        end={to === '/'}
                        className={({ isActive }) =>
                            `flex items-center gap-3 px-4 py-3 rounded-lg mb-1 transition-colors text-sm font-medium ${
                                isActive
                                    ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                                    : 'text-sidebar-foreground/80 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground'
                            }`
                        }
                    >
                        <Icon className="w-5 h-5" />
                        {label}
                    </NavLink>
                ))}
            </nav>
        </aside>
    );
}
