import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/lib/AuthContext';

// Layout
import AppLayout from '@/components/layout/AppLayout';

// Core Studio & Pages
import ContractStudio from '@/components/dashboard/ContractStudio';
import Dashboard from '@/pages/Dashboard';
import DocumentLibrary from '@/pages/DocumentLibrary';
import UploadStudio from '@/pages/UploadStudio';
import ComparisonStudio from '@/pages/ComparisonStudio';
import PlaybookStudio from '@/pages/PlaybookStudio';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="documents" element={<DocumentLibrary />} />
            <Route path="upload" element={<UploadStudio />} />
            <Route path="review/:id" element={<ContractStudio />} />
            <Route path="compare" element={<ComparisonStudio />} />
            <Route path="playbook" element={<PlaybookStudio />} />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
