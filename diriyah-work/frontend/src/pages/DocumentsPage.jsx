import React, { useState } from 'react';
import DocumentUpload from '../components/DocumentUpload';

export default function DocumentsPage() {
  const [recentUploads, setRecentUploads] = useState([]);

  const handleUploadComplete = () => {
    // Refresh recent uploads list
    setRecentUploads(prev => [...prev, { id: Date.now(), name: 'New upload', date: new Date().toISOString() }]);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-4xl space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Document Management</h1>
          <p className="text-gray-500">Upload and classify construction documents</p>
        </div>

        {/* Upload Section */}
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">Upload Documents</h2>
          <DocumentUpload 
            projectId="heritage-quarter"
            onUploadComplete={handleUploadComplete}
          />
        </div>

        {/* Document Types Info */}
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">Supported Document Types</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[
              { icon: '📄', name: 'Contracts', desc: 'Legal agreements and contracts' },
              { icon: '📐', name: 'Drawings', desc: 'CAD and architectural drawings' },
              { icon: '❓', name: 'RFIs', desc: 'Requests for Information' },
              { icon: '📋', name: 'Submittals', desc: 'Shop drawings and samples' },
              { icon: '📝', name: 'Meeting Minutes', desc: 'Meeting notes and actions' },
              { icon: '📊', name: 'Reports', desc: 'Progress and status reports' },
              { icon: '💰', name: 'Invoices', desc: 'Payment documents' },
              { icon: '📅', name: 'Schedules', desc: 'Project schedules' },
              { icon: '🔄', name: 'Change Orders', desc: 'Scope changes and variations' },
            ].map((type) => (
              <div key={type.name} className="flex items-start gap-3 rounded-lg bg-gray-50 p-3">
                <span className="text-2xl">{type.icon}</span>
                <div>
                  <p className="font-medium text-gray-900">{type.name}</p>
                  <p className="text-sm text-gray-500">{type.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* AI Classification Info */}
        <div className="rounded-lg border border-[#a67c52]/30 bg-[#f6efe6] p-6">
          <div className="flex items-start gap-4">
            <span className="text-3xl">🤖</span>
            <div>
              <h3 className="font-semibold text-gray-900">AI-Powered Classification</h3>
              <p className="mt-1 text-sm text-gray-700">
                Diriyah AI automatically classifies your documents, extracts key information, 
                and makes them searchable. Upload any construction document and our AI will 
                identify its type, extract action items, and link it to relevant project data.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
