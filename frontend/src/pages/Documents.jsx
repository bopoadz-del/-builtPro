import React, { useState, useEffect } from 'react';
import { Upload, Download, Search, Filter, FileText, Image, File, Folder, Eye, Trash2, Share2, Star } from 'lucide-react';

const Documents = () => {
  const [documents, setDocuments] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [viewMode, setViewMode] = useState('grid');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDocuments();
  }, [filterType]);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filterType !== 'all') params.append('type', filterType);

      const response = await fetch(`/api/v1/documents?${params}`);
      const data = await response.json();
      setDocuments(data.items || []);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
      // Mock data
      setDocuments([
        {
          id: 1,
          name: 'Structural Drawings - Building A.pdf',
          type: 'pdf',
          size: '12.5 MB',
          category: 'Drawings',
          uploaded_by: 'John Doe',
          uploaded_at: new Date().toISOString(),
          thumbnail: 'https://via.placeholder.com/200x150',
          starred: true,
        },
        {
          id: 2,
          name: 'Material Submittal - Concrete.docx',
          type: 'document',
          size: '2.3 MB',
          category: 'Submittals',
          uploaded_by: 'Jane Smith',
          uploaded_at: new Date(Date.now() - 86400000).toISOString(),
          thumbnail: 'https://via.placeholder.com/200x150',
          starred: false,
        },
        {
          id: 3,
          name: 'Site Photo - Foundation Work.jpg',
          type: 'image',
          size: '4.8 MB',
          category: 'Photos',
          uploaded_by: 'Mike Johnson',
          uploaded_at: new Date(Date.now() - 172800000).toISOString(),
          thumbnail: 'https://via.placeholder.com/200x150',
          starred: false,
        },
        {
          id: 4,
          name: 'MEP Coordination Report.xlsx',
          type: 'spreadsheet',
          size: '1.2 MB',
          category: 'Reports',
          uploaded_by: 'Sarah Lee',
          uploaded_at: new Date(Date.now() - 259200000).toISOString(),
          thumbnail: 'https://via.placeholder.com/200x150',
          starred: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const filteredDocuments = documents.filter(doc =>
    doc.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.category?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getFileIcon = (type) => {
    switch (type) {
      case 'pdf':
        return <FileText className="w-8 h-8 text-red-600" />;
      case 'image':
        return <Image className="w-8 h-8 text-blue-600" />;
      case 'document':
        return <FileText className="w-8 h-8 text-blue-600" />;
      case 'spreadsheet':
        return <FileText className="w-8 h-8 text-green-600" />;
      default:
        return <File className="w-8 h-8 text-gray-600" />;
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/v1/documents/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      fetchDocuments();
      alert('Document uploaded successfully!');
    } catch (error) {
      alert('Failed to upload document');
    }
  };

  const toggleStar = async (docId) => {
    const doc = documents.find(d => d.id === docId);
    if (!doc) return;

    try {
      await fetch(`/api/v1/documents/${docId}/star`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ starred: !doc.starred }),
      });
      setDocuments(documents.map(d =>
        d.id === docId ? { ...d, starred: !d.starred } : d
      ));
    } catch (error) {
      console.error('Failed to toggle star:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Documents</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage project documents, drawings, and submittals
          </p>
        </div>
        <label className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer">
          <Upload className="w-5 h-5" />
          Upload Document
          <input
            type="file"
            onChange={handleFileUpload}
            className="hidden"
          />
        </label>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Documents</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {documents.length}
              </p>
            </div>
            <FileText className="w-8 h-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">PDFs</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {documents.filter(d => d.type === 'pdf').length}
              </p>
            </div>
            <FileText className="w-8 h-8 text-red-600" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Images</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {documents.filter(d => d.type === 'image').length}
              </p>
            </div>
            <Image className="w-8 h-8 text-purple-600" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Starred</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {documents.filter(d => d.starred).length}
              </p>
            </div>
            <Star className="w-8 h-8 text-yellow-600" />
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div className="flex gap-2">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Types</option>
              <option value="pdf">PDF</option>
              <option value="image">Images</option>
              <option value="document">Documents</option>
              <option value="spreadsheet">Spreadsheets</option>
            </select>

            <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <Filter className="w-5 h-5" />
              More Filters
            </button>

            <div className="flex border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
              <button
                onClick={() => setViewMode('grid')}
                className={`px-3 py-2 ${viewMode === 'grid' ? 'bg-blue-600 text-white' : 'hover:bg-gray-50 dark:hover:bg-gray-700'}`}
              >
                Grid
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`px-3 py-2 ${viewMode === 'list' ? 'bg-blue-600 text-white' : 'hover:bg-gray-50 dark:hover:bg-gray-700'}`}
              >
                List
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Documents Display */}
      {loading ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center text-gray-500 dark:text-gray-400">
          Loading documents...
        </div>
      ) : filteredDocuments.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center text-gray-500 dark:text-gray-400">
          No documents found
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {filteredDocuments.map((doc) => (
            <div
              key={doc.id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg transition-shadow overflow-hidden"
            >
              {/* Thumbnail */}
              <div className="h-48 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 flex items-center justify-center">
                {getFileIcon(doc.type)}
              </div>

              {/* Content */}
              <div className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate flex-1">
                    {doc.name}
                  </h3>
                  <button
                    onClick={() => toggleStar(doc.id)}
                    className="flex-shrink-0 ml-2"
                  >
                    <Star
                      className={`w-4 h-4 ${
                        doc.starred
                          ? 'text-yellow-500 fill-yellow-500'
                          : 'text-gray-400 hover:text-yellow-500'
                      }`}
                    />
                  </button>
                </div>

                <div className="space-y-1 mb-3">
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {doc.category} • {doc.size}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Uploaded by {doc.uploaded_by}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {new Date(doc.uploaded_at).toLocaleDateString()}
                  </p>
                </div>

                <div className="flex gap-1">
                  <button className="flex-1 px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors flex items-center justify-center gap-1">
                    <Eye className="w-3 h-3" />
                    View
                  </button>
                  <button className="px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                    <Download className="w-3 h-3" />
                  </button>
                  <button className="px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                    <Share2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Category</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Size</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Uploaded</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredDocuments.map((doc) => (
                <tr key={doc.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-3">
                      {getFileIcon(doc.type)}
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">{doc.name}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{doc.uploaded_by}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {doc.category}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {doc.size}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {new Date(doc.uploaded_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <div className="flex gap-2">
                      <button className="text-blue-600 hover:text-blue-800">View</button>
                      <button className="text-gray-600 hover:text-gray-800">Download</button>
                      <button className="text-red-600 hover:text-red-800">Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default Documents;
