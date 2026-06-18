import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import CrimeMap from './pages/CrimeMap';
import NetworkAnalysis from './pages/NetworkAnalysis';
import Analytics from './pages/Analytics';
import Offenders from './pages/Offenders';
import Alerts from './pages/Alerts';
import Reports from './pages/Reports';
import Admin from './pages/Admin';
import LoginPage from './pages/Login';

const ProtectedRoute = ({ children }) => {
  const { user } = useAuthStore();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="flex min-h-screen bg-navy">
      <Sidebar />
      <div className="flex-1 flex flex-col md:ml-64 min-h-screen">
        <Header />
        <main className="flex-1 min-h-0 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
};

function App() {
  const { user, refresh } = useAuthStore();

  useEffect(() => {
    // On app load, try to refresh token to restore session
    const token = localStorage.getItem('token');
    if (token && !user) {
      refresh();
    }
  }, []);

  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        
        <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/map" element={<ProtectedRoute><CrimeMap /></ProtectedRoute>} />
        <Route path="/network" element={<ProtectedRoute><NetworkAnalysis /></ProtectedRoute>} />
        <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
        <Route path="/offenders" element={<ProtectedRoute><Offenders /></ProtectedRoute>} />
        <Route path="/alerts" element={<ProtectedRoute><Alerts /></ProtectedRoute>} />
        <Route path="/reports" element={<ProtectedRoute><Reports /></ProtectedRoute>} />
        <Route path="/admin" element={<ProtectedRoute><Admin /></ProtectedRoute>} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
