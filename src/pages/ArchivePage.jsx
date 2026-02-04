import React from 'react';
import FileUpload from '../components/FileUpload.jsx';

/**
 * ArchivePage wraps the FileUpload component to inspect archive files.
 * The backend returns the contents of ZIP or TAR archives. Unsupported
 * formats produce an informative error.
 */
export default function ArchivePage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Archive Inspection</h1>
      <p className="mb-4 text-gray-700">
        Upload a ZIP or TAR archive to list its contents. Only the high level
        metadata is returned in this stub implementation.
      </p>
      <FileUpload
        title="Analyze Archive (ZIP/TAR)"
        endpoint="/api/v1/archive/analyze"
        accept="application/zip,application/x-tar,application/x-gtar"
      />
    </div>
  );
}