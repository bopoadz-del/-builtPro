// Main App Component with Routing - ITEM 87
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import Dashboard from './pages/Dashboard';
import { Toaster } from 'react-hot-toast';

// Keep existing auth pages
import LoginPage from './pages/LoginPage.jsx';
import RegisterPage from './pages/RegisterPage.jsx';

function App() {
  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: {
            background: '#363636',
            color: '#fff',
          },
        }}
      />

      <Routes>
        {/* Auth routes (no layout) */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Main app routes (with layout) */}
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="*" element={
            <div className="text-center py-12">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Page Not Found</h2>
              <p className="text-gray-600 dark:text-gray-400 mt-2">The page you're looking for doesn't exist.</p>
            </div>
          } />
        </Route>
      </Routes>
    </>
  );
}

export default App;
