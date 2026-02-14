import React, { useState, useEffect, useRef } from 'react';
import { Upload, Download, Maximize2, ZoomIn, ZoomOut, RotateCw, Eye, EyeOff, Layers, Ruler, AlertTriangle } from 'lucide-react';

const BIMViewer = () => {
  const [ifcFiles, setIfcFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [viewerSettings, setViewerSettings] = useState({
    showGrid: true,
    showAxes: true,
    showDimensions: false,
    wireframe: false,
    perspective: true,
  });
  const [layers, setLayers] = useState([]);
  const [clashes, setClashes] = useState([]);
  const canvasRef = useRef(null);

  useEffect(() => {
    fetchIFCFiles();
  }, []);

  useEffect(() => {
    if (selectedFile) {
      loadIFCModel(selectedFile);
    }
  }, [selectedFile]);

  const fetchIFCFiles = async () => {
    try {
      const response = await fetch('/api/v1/bim/ifc-files');
      const data = await response.json();
      setIfcFiles(data.items || []);
    } catch (error) {
      console.error('Failed to fetch IFC files:', error);
      // Mock data
      setIfcFiles([
        { id: 1, name: 'Building-A-Structure.ifc', size: '25 MB', uploaded: new Date().toISOString() },
        { id: 2, name: 'Building-A-MEP.ifc', size: '18 MB', uploaded: new Date().toISOString() },
        { id: 3, name: 'Building-B-Architecture.ifc', size: '42 MB', uploaded: new Date().toISOString() },
      ]);
    }
  };

  const loadIFCModel = async (file) => {
    try {
      const response = await fetch(`/api/v1/bim/load-ifc/${file.id}`);
      const data = await response.json();

      setLayers(data.layers || [
        { id: 1, name: 'Walls', visible: true, count: 150 },
        { id: 2, name: 'Doors', visible: true, count: 45 },
        { id: 3, name: 'Windows', visible: true, count: 80 },
        { id: 4, name: 'Slabs', visible: true, count: 30 },
        { id: 5, name: 'Columns', visible: true, count: 120 },
        { id: 6, name: 'MEP Systems', visible: false, count: 200 },
      ]);

      setClashes(data.clashes || [
        { id: 1, type: 'Hard Clash', elements: ['Wall-001', 'Duct-045'], severity: 'high' },
        { id: 2, type: 'Soft Clash', elements: ['Door-023', 'Pipe-112'], severity: 'medium' },
      ]);

      // Initialize 3D viewer (placeholder - would use Three.js/WebGL in production)
      initializeViewer();
    } catch (error) {
      console.error('Failed to load IFC model:', error);
    }
  };

  const initializeViewer = () => {
    // Placeholder for 3D viewer initialization
    // In production, this would use Three.js, Babylon.js, or a dedicated IFC viewer library
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#1a1a1a';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#4a90e2';
      ctx.font = '20px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('3D BIM Viewer', canvas.width / 2, canvas.height / 2 - 20);
      ctx.fillStyle = '#888';
      ctx.font = '14px Arial';
      ctx.fillText('IFC model would be rendered here using Three.js/WebGL', canvas.width / 2, canvas.height / 2 + 10);
      ctx.fillText(`Selected: ${selectedFile?.name}`, canvas.width / 2, canvas.height / 2 + 40);
    }
  };

  const toggleLayer = (layerId) => {
    setLayers(layers.map(layer =>
      layer.id === layerId ? { ...layer, visible: !layer.visible } : layer
    ));
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/v1/bim/upload-ifc', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      fetchIFCFiles();
      alert('IFC file uploaded successfully!');
    } catch (error) {
      alert('Failed to upload IFC file');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">BIM Viewer</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            View and analyze IFC/BIM models in 3D
          </p>
        </div>
        <div className="flex gap-2">
          <label className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer">
            <Upload className="w-5 h-5" />
            Upload IFC
            <input
              type="file"
              accept=".ifc"
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
          {selectedFile && (
            <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <Download className="w-5 h-5" />
              Export
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* File Browser Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              IFC Files
            </h2>
            <div className="space-y-2">
              {ifcFiles.map((file) => (
                <div
                  key={file.id}
                  onClick={() => setSelectedFile(file)}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                    selectedFile?.id === file.id
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-blue-300'
                  }`}
                >
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {file.size}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Layers Panel */}
          {selectedFile && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mt-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <Layers className="w-5 h-5" />
                Layers
              </h2>
              <div className="space-y-2">
                {layers.map((layer) => (
                  <div
                    key={layer.id}
                    className="flex items-center justify-between p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded"
                  >
                    <div className="flex items-center gap-2 flex-1">
                      <button onClick={() => toggleLayer(layer.id)}>
                        {layer.visible ? (
                          <Eye className="w-4 h-4 text-blue-600" />
                        ) : (
                          <EyeOff className="w-4 h-4 text-gray-400" />
                        )}
                      </button>
                      <span className="text-sm text-gray-900 dark:text-white">
                        {layer.name}
                      </span>
                    </div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {layer.count}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Clashes Panel */}
          {clashes.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mt-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-600" />
                Clashes ({clashes.length})
              </h2>
              <div className="space-y-2">
                {clashes.map((clash) => (
                  <div
                    key={clash.id}
                    className="p-3 border border-gray-200 dark:border-gray-700 rounded-lg"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {clash.type}
                      </span>
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        clash.severity === 'high'
                          ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                          : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                      }`}>
                        {clash.severity}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      {clash.elements.join(' ↔ ')}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 3D Viewer */}
        <div className="lg:col-span-3">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
            {/* Toolbar */}
            <div className="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600 p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <button className="p-2 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors" title="Zoom In">
                    <ZoomIn className="w-5 h-5" />
                  </button>
                  <button className="p-2 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors" title="Zoom Out">
                    <ZoomOut className="w-5 h-5" />
                  </button>
                  <button className="p-2 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors" title="Reset View">
                    <RotateCw className="w-5 h-5" />
                  </button>
                  <button className="p-2 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors" title="Fullscreen">
                    <Maximize2 className="w-5 h-5" />
                  </button>
                  <button className="p-2 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors" title="Measure">
                    <Ruler className="w-5 h-5" />
                  </button>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={viewerSettings.showGrid}
                      onChange={(e) => setViewerSettings({ ...viewerSettings, showGrid: e.target.checked })}
                      className="rounded"
                    />
                    <span className="text-gray-700 dark:text-gray-300">Grid</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={viewerSettings.wireframe}
                      onChange={(e) => setViewerSettings({ ...viewerSettings, wireframe: e.target.checked })}
                      className="rounded"
                    />
                    <span className="text-gray-700 dark:text-gray-300">Wireframe</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Canvas */}
            <div className="bg-gray-900 relative">
              {selectedFile ? (
                <canvas
                  ref={canvasRef}
                  width={1200}
                  height={700}
                  className="w-full h-auto"
                />
              ) : (
                <div className="flex items-center justify-center h-96 text-gray-500 dark:text-gray-400">
                  <div className="text-center">
                    <Upload className="w-16 h-16 mx-auto mb-4 opacity-50" />
                    <p className="text-lg">No IFC file selected</p>
                    <p className="text-sm mt-2">Select a file from the sidebar or upload a new one</p>
                  </div>
                </div>
              )}
            </div>

            {/* Info Bar */}
            {selectedFile && (
              <div className="bg-gray-50 dark:bg-gray-700 border-t border-gray-200 dark:border-gray-600 p-3">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-6">
                    <span className="text-gray-600 dark:text-gray-400">
                      File: <strong className="text-gray-900 dark:text-white">{selectedFile.name}</strong>
                    </span>
                    <span className="text-gray-600 dark:text-gray-400">
                      Elements: <strong className="text-gray-900 dark:text-white">
                        {layers.reduce((sum, layer) => sum + layer.count, 0)}
                      </strong>
                    </span>
                    <span className="text-gray-600 dark:text-gray-400">
                      Visible Layers: <strong className="text-gray-900 dark:text-white">
                        {layers.filter(l => l.visible).length}/{layers.length}
                      </strong>
                    </span>
                  </div>
                  <div className="text-gray-600 dark:text-gray-400">
                    Camera: Perspective
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BIMViewer;
