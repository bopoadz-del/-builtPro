import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar.jsx';
import LoginPage from './pages/LoginPage.jsx';
import RegisterPage from './pages/RegisterPage.jsx';
import DashboardPage from './pages/DashboardPage.jsx';
import AnalyticsPage from './pages/AnalyticsPage.jsx';
import ConnectorsPage from './pages/ConnectorsPage.jsx';
import QTOPage from './pages/QTOPage.jsx';
import TranslationPage from './pages/TranslationPage.jsx';
import ReasoningPage from './pages/ReasoningPage.jsx';
import VisionPage from './pages/VisionPage.jsx';
import SchedulePage from './pages/SchedulePage.jsx';
import AudioPage from './pages/AudioPage.jsx';
import ArchivePage from './pages/ArchivePage.jsx';
import CadPage from './pages/CadPage.jsx';
import ChatPage from './pages/ChatPage.jsx';
import CodePage from './pages/CodePage.jsx';

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
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/connectors" element={<ConnectorsPage />} />
          <Route path="/qto" element={<QTOPage />} />
          <Route path="/translation" element={<TranslationPage />} />
          <Route path="/reasoning" element={<ReasoningPage />} />
          <Route path="/vision" element={<VisionPage />} />
          <Route path="/schedule" element={<SchedulePage />} />
          <Route path="/audio" element={<AudioPage />} />
          <Route path="/archive" element={<ArchivePage />} />
          <Route path="/cad" element={<CadPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/code" element={<CodePage />} />
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