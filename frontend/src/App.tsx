import './index.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Upload } from './pages/Upload';
import { Dashboard } from './pages/Dashboard';
import { Exceptions } from './pages/Exceptions';
import { Settings } from './pages/Settings';
import { AuditLog } from './pages/AuditLog';
import { Analytics } from './pages/Analytics';
import { DocumentReview } from './pages/DocumentReview';

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route element={<Layout />}>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/exceptions" element={<Exceptions />} />
                    <Route path="/upload" element={<Upload />} />
                    <Route path="/analytics" element={<Analytics />} />
                    <Route path="/audit" element={<AuditLog />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="/document/:id" element={<DocumentReview />} />
                </Route>
            </Routes>
        </BrowserRouter>
    );
}

export default App;

