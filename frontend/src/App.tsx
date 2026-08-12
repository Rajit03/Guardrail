import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import DashboardLayout from './layouts/DashboardLayout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import RepositoriesPage from './pages/RepositoriesPage';
import AddRepositoryPage from './pages/AddRepositoryPage';
import RepositoryDetailsPage from './pages/RepositoryDetailsPage';
import EditRepositoryPage from './pages/EditRepositoryPage';
import FindingsPage from './pages/FindingsPage';
import FindingDetailsPage from './pages/FindingDetailsPage';

export const App: React.FC = () => {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public Authentication Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected Application Routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/repositories" element={<RepositoriesPage />} />
              <Route path="/repositories/new" element={<AddRepositoryPage />} />
              <Route path="/repositories/:id" element={<RepositoryDetailsPage />} />
              <Route path="/repositories/:id/edit" element={<EditRepositoryPage />} />
              <Route path="/findings" element={<FindingsPage />} />
              <Route path="/findings/:id" element={<FindingDetailsPage />} />
            </Route>
          </Route>

          {/* Fallback & Redirects */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
};

export default App;
