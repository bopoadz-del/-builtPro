import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar.jsx';
import LoginPage from './pages/LoginPage.jsx';
import RegisterPage from './pages/RegisterPage.jsx';
import DashboardPage from './pages/DashboardPage.jsx';

// The root application component defines the navigation bar and client‑side
// routes.  Users are redirected to the dashboard once authenticated.
function App() {
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className="flex-1 container mx-auto px-4 py-8">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          {/* Redirect from root to dashboard.  In a more complex application you
              could show a landing page or marketing content instead. */}
          <Route path="/" element={<Navigate to="/dashboard" />} />
          {/* Catch all unknown paths */}
          <Route path="*" element={<p className="text-center">Page not found</p>} />
        </Routes>
      </main>
    </div>
  );
}

export default App;