import React from 'react';
import FileUpload from '../components/FileUpload.jsx';

/**
 * DashboardPage aggregates the various analysis tools exposed by the backend
 * into a single screen.  Each section leverages the FileUpload component
 * to send a file to the appropriate API endpoint and display the
 * response.  Additional widgets (e.g. chat or self‑coding) could be
 * integrated here in the future.
 */
export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <p className="mb-8 text-gray-700">
        Upload files for analysis using the tools below.  Results will be
        displayed as structured JSON.  For PDF uploads a preview of the
        first page is shown when available.
      </p>
      <FileUpload
        title="Analyze PDF Document"
        endpoint="/api/v1/pdf/analyze"
        accept="application/pdf"
      />
      <FileUpload
        title="Transcribe Audio Recording"
        endpoint="/api/v1/audio/transcribe"
        accept="audio/*"
      />
      <FileUpload
        title="Analyze Archive (ZIP)"
        endpoint="/api/v1/archive/analyze"
        accept="application/zip"
      />
      <FileUpload
        title="Analyze CAD File"
        endpoint="/api/v1/cad/analyze"
        accept="application/octet-stream,.dwg,.dxf"
      />
      <FileUpload
        title="Analyze Schedule File"
        endpoint="/api/v1/schedule/analyze"
        accept=".xer,.xml,.mpp,application/xml,text/xml,application/octet-stream"
      />
    </div>
  );
}