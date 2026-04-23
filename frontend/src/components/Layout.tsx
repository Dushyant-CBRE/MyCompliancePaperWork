import { Outlet } from 'react-router-dom';
import { SideNav } from './SideNav';
import { Header } from './Header';

export function Layout() {
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
