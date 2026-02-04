import React from 'react';
import FileUpload from '../components/FileUpload.jsx';

/**
 * CadPage wraps the FileUpload component to analyse CAD/3D model files.
 * Only basic metadata is returned; heavy geometry processing is out of
 * scope for this stubbed implementation.
 */
export default function CadPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">CAD/Model Analysis</h1>
      <p className="mb-4 text-gray-700">
        Upload a CAD or 3D model file (DWG, DXF, etc.) to extract basic
        metadata. Detailed geometry insights are not implemented.
      </p>
      <FileUpload
        title="Analyze CAD File"
        endpoint="/api/v1/cad/analyze"
        accept=".dwg,.dxf,application/octet-stream"
      />
    </div>
  );
}