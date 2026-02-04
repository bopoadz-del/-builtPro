import React, { useState, useEffect, useMemo } from 'react';

/**
 * BIMViewer - Interactive BIM/IFC model viewer
 * 
 * Features:
 * - File upload for IFC files
 * - Element hierarchy tree
 * - Element details panel
 * - Quantity summary
 * - Filter by type/level
 */

const ElementIcon = ({ type }) => {
  const icons = {
    IfcWall: '🧱',
    IfcColumn: '🏛️',
    IfcBeam: '📏',
    IfcSlab: '⬜',
    IfcDoor: '🚪',
    IfcWindow: '🪟',
    IfcStair: '🪜',
    IfcRoof: '🏠',
    IfcFooting: '🔲',
    IfcPipeSegment: '🔧',
    IfcFurniture: '🪑',
    default: '📦',
  };
  return <span>{icons[type] || icons.default}</span>;
};

const CategoryBadge = ({ category }) => {
  const colors = {
    Structural: 'bg-blue-100 text-blue-800',
    Architectural: 'bg-green-100 text-green-800',
    MEP: 'bg-orange-100 text-orange-800',
    Site: 'bg-yellow-100 text-yellow-800',
    Furniture: 'bg-purple-100 text-purple-800',
    Other: 'bg-gray-100 text-gray-800',
  };
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${colors[category] || colors.Other}`}>
      {category}
    </span>
  );
};

const StatCard = ({ label, value, icon }) => (
  <div className="rounded-lg border border-gray-200 bg-white p-4">
    <div className="flex items-center gap-3">
      <span className="text-2xl">{icon}</span>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  </div>
);

const ElementRow = ({ element, onClick, isSelected }) => (
  <tr
    onClick={() => onClick(element)}
    className={`cursor-pointer transition-colors ${
      isSelected ? 'bg-[#f6efe6]' : 'hover:bg-gray-50'
    }`}
  >
    <td className="whitespace-nowrap px-4 py-3">
      <div className="flex items-center gap-2">
        <ElementIcon type={element.ifc_type} />
        <span className="font-medium text-gray-900">{element.name || 'Unnamed'}</span>
      </div>
    </td>
    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
      {element.ifc_type.replace('Ifc', '')}
    </td>
    <td className="whitespace-nowrap px-4 py-3">
      <CategoryBadge category={element.category} />
    </td>
    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
      {element.level || '-'}
    </td>
  </tr>
);

const ElementDetails = ({ element, onClose }) => {
  if (!element) return null;

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <h3 className="font-semibold text-gray-900">Element Details</h3>
        <button
          onClick={onClose}
          className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="space-y-4 p-4">
        <div className="flex items-center gap-3">
          <span className="text-3xl"><ElementIcon type={element.ifc_type} /></span>
          <div>
            <p className="font-semibold text-gray-900">{element.name || 'Unnamed Element'}</p>
            <p className="text-sm text-gray-500">{element.ifc_type}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-gray-500">Category</p>
            <p className="font-medium"><CategoryBadge category={element.category} /></p>
          </div>
          <div>
            <p className="text-gray-500">Level</p>
            <p className="font-medium text-gray-900">{element.level || 'Not assigned'}</p>
          </div>
          <div>
            <p className="text-gray-500">Material</p>
            <p className="font-medium text-gray-900">{element.material || 'Not specified'}</p>
          </div>
          <div>
            <p className="text-gray-500">Global ID</p>
            <p className="font-mono text-xs text-gray-600 truncate">{element.global_id}</p>
          </div>
        </div>

        {element.description && (
          <div>
            <p className="text-sm text-gray-500">Description</p>
            <p className="text-sm text-gray-900">{element.description}</p>
          </div>
        )}

        {element.properties && element.properties.length > 0 && (
          <div>
            <p className="mb-2 text-sm font-medium text-gray-700">Properties</p>
            <div className="max-h-40 overflow-y-auto rounded border border-gray-200">
              {element.properties.map((pset, idx) => (
                <div key={idx} className="border-b border-gray-100 p-2 last:border-0">
                  <p className="text-xs font-medium text-gray-600">{pset.name}</p>
                  {Object.entries(pset.properties || {}).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-xs">
                      <span className="text-gray-500">{key}</span>
                      <span className="font-medium">{String(value)}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}

        {element.quantities && element.quantities.length > 0 && (
          <div>
            <p className="mb-2 text-sm font-medium text-gray-700">Quantities</p>
            <div className="space-y-1">
              {element.quantities.map((q, idx) => (
                <div key={idx} className="flex justify-between rounded bg-gray-50 px-3 py-2 text-sm">
                  <span className="text-gray-600">{q.name}</span>
                  <span className="font-medium">{q.value} {q.unit}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default function BIMViewer({ projectId }) {
  const [modelData, setModelData] = useState(null);
  const [elements, setElements] = useState([]);
  const [selectedElement, setSelectedElement] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState({ type: '', level: '', search: '' });
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const uploadIFC = async (file) => {
    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/ifc/parse', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to parse IFC file');
      }

      const data = await response.json();
      setModelData(data);

      // Fetch elements
      const elemResponse = await fetch(`/api/ifc/${data.model_id}/elements?page_size=500`);
      if (elemResponse.ok) {
        const elemData = await elemResponse.json();
        setElements(elemData.elements);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredElements = useMemo(() => {
    return elements.filter((elem) => {
      if (filter.type && elem.ifc_type !== filter.type) return false;
      if (filter.level && elem.level !== filter.level) return false;
      if (filter.search) {
        const search = filter.search.toLowerCase();
        return (
          (elem.name && elem.name.toLowerCase().includes(search)) ||
          elem.ifc_type.toLowerCase().includes(search) ||
          elem.global_id.toLowerCase().includes(search)
        );
      }
      return true;
    });
  }, [elements, filter]);

  const paginatedElements = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredElements.slice(start, start + pageSize);
  }, [filteredElements, page]);

  const uniqueTypes = useMemo(() => 
    [...new Set(elements.map(e => e.ifc_type))].sort(),
    [elements]
  );

  const uniqueLevels = useMemo(() => 
    [...new Set(elements.map(e => e.level).filter(Boolean))].sort(),
    [elements]
  );

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file && file.name.toLowerCase().endsWith('.ifc')) {
      uploadIFC(file);
    } else {
      setError('Please select a valid IFC file');
    }
  };

  if (!modelData) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 bg-gray-50 p-12">
        <div className="mb-4 rounded-full bg-gray-200 p-4">
          <svg className="h-12 w-12 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
        </div>
        
        <h3 className="mb-2 text-lg font-semibold text-gray-900">Load BIM Model</h3>
        <p className="mb-4 text-sm text-gray-500">Upload an IFC file to visualize building elements</p>

        <label className="cursor-pointer rounded-lg bg-[#a67c52] px-6 py-3 font-semibold text-white shadow-sm transition-colors hover:bg-[#8b6844]">
          <input
            type="file"
            accept=".ifc"
            onChange={handleFileSelect}
            className="hidden"
          />
          Select IFC File
        </label>

        {isLoading && (
          <div className="mt-4 flex items-center gap-2 text-sm text-gray-500">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-[#a67c52]" />
            Parsing IFC file...
          </div>
        )}

        {error && (
          <p className="mt-4 text-sm text-red-600">{error}</p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Model Info Header */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {modelData.model_info?.project_name || 'BIM Model'}
            </h2>
            <p className="text-sm text-gray-500">
              {modelData.model_info?.building_name} • {modelData.model_info?.schema_version}
            </p>
          </div>
          <label className="cursor-pointer rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
            <input
              type="file"
              accept=".ifc"
              onChange={handleFileSelect}
              className="hidden"
            />
            Load New Model
          </label>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Total Elements" value={modelData.total_elements} icon="📦" />
        <StatCard label="Element Types" value={Object.keys(modelData.element_counts).length} icon="🏗️" />
        <StatCard label="Levels" value={modelData.levels?.length || 0} icon="🏢" />
        <StatCard label="Materials" value={modelData.materials?.length || 0} icon="🎨" />
      </div>

      {/* Element Counts by Type */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h3 className="mb-3 font-semibold text-gray-900">Elements by Type</h3>
        <div className="flex flex-wrap gap-2">
          {Object.entries(modelData.element_counts || {}).map(([type, count]) => (
            <button
              key={type}
              onClick={() => setFilter(f => ({ ...f, type: f.type === type ? '' : type }))}
              className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-sm transition-colors ${
                filter.type === type
                  ? 'bg-[#a67c52] text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <ElementIcon type={type} />
              <span>{type.replace('Ifc', '')}</span>
              <span className="rounded-full bg-white/20 px-1.5 text-xs">{count}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Elements Table */}
        <div className="lg:col-span-2">
          <div className="rounded-lg border border-gray-200 bg-white">
            {/* Filters */}
            <div className="flex flex-wrap items-center gap-3 border-b border-gray-200 p-4">
              <input
                type="text"
                placeholder="Search elements..."
                value={filter.search}
                onChange={(e) => setFilter(f => ({ ...f, search: e.target.value }))}
                className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-[#a67c52] focus:outline-none"
              />
              <select
                value={filter.level}
                onChange={(e) => setFilter(f => ({ ...f, level: e.target.value }))}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-[#a67c52] focus:outline-none"
              >
                <option value="">All Levels</option>
                {uniqueLevels.map(level => (
                  <option key={level} value={level}>{level}</option>
                ))}
              </select>
              {(filter.type || filter.level || filter.search) && (
                <button
                  onClick={() => setFilter({ type: '', level: '', search: '' })}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Clear filters
                </button>
              )}
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 text-left text-sm text-gray-500">
                  <tr>
                    <th className="px-4 py-3 font-medium">Name</th>
                    <th className="px-4 py-3 font-medium">Type</th>
                    <th className="px-4 py-3 font-medium">Category</th>
                    <th className="px-4 py-3 font-medium">Level</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {paginatedElements.map((element) => (
                    <ElementRow
                      key={element.global_id}
                      element={element}
                      onClick={setSelectedElement}
                      isSelected={selectedElement?.global_id === element.global_id}
                    />
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between border-t border-gray-200 px-4 py-3">
              <p className="text-sm text-gray-500">
                Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, filteredElements.length)} of {filteredElements.length}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="rounded border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={page * pageSize >= filteredElements.length}
                  className="rounded border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Details Panel */}
        <div>
          {selectedElement ? (
            <ElementDetails
              element={selectedElement}
              onClose={() => setSelectedElement(null)}
            />
          ) : (
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
              <p className="text-sm text-gray-500">
                Select an element to view details
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
