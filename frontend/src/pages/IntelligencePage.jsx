import React from 'react';
import ProjectIntelligenceDashboard from '../components/ProjectIntelligenceDashboard';

export default function IntelligencePage() {
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <ProjectIntelligenceDashboard projectId="heritage-quarter" />
    </div>
  );
}
