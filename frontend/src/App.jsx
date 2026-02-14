// Main App Component with Routing - ITEM 87
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import Dashboard from './pages/Dashboard';
import { Toaster } from 'react-hot-toast';

// Keep existing auth pages
import LoginPage from './pages/LoginPage.jsx';
import RegisterPage from './pages/RegisterPage.jsx';

// Phase 2.2 - Core UI Pages (Items 66-86)
import Registry from './pages/Registry';
import Learning from './pages/Learning';
import Sandbox from './pages/Sandbox';
import Audit from './pages/Audit';
import Pipelines from './pages/Pipelines';
import Settings from './pages/Settings';
import Tasks from './pages/Tasks';
import BIMViewer from './pages/BIMViewer';
import ActionItems from './pages/ActionItems';
import Documents from './pages/Documents';
import Chat from './pages/Chat';
import Analytics from './pages/Analytics';
import Admin from './pages/Admin';
import Economics from './pages/Economics';

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

          {/* Core Pages */}
          <Route path="registry" element={<Registry />} />
          <Route path="learning" element={<Learning />} />
          <Route path="sandbox" element={<Sandbox />} />
          <Route path="audit" element={<Audit />} />
          <Route path="pipelines" element={<Pipelines />} />
          <Route path="settings" element={<Settings />} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="bim-viewer" element={<BIMViewer />} />
          <Route path="action-items" element={<ActionItems />} />
          <Route path="documents" element={<Documents />} />
          <Route path="chat" element={<Chat />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="admin" element={<Admin />} />
          <Route path="economics" element={<Economics />} />

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
