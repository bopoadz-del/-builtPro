import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar.jsx';
import LoginPage from './pages/LoginPage.jsx';
import RegisterPage from './pages/RegisterPage.jsx';
import { DashboardEnhanced } from './pages/DashboardEnhanced';

function App() {
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/dashboard" element={<DashboardEnhanced />} />
          <Route path="/chat" element={<DashboardEnhanced />} />
          <Route path="/" element={<Navigate to="/dashboard" />} />
          <Route path="*" element={<p className="text-center">Page not found</p>} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
