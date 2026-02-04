import React, { useState } from 'react';

/**
 * Reusable file upload component.  It renders a file input, an upload button,
 * and displays the JSON response from the server.  For analysis endpoints
 * that return a thumbnail field the component will render a preview image.
 *
 * Props:
 *   - title: Heading to display above the form.
 *   - endpoint: API path (including leading /api) that accepts a file upload.
 *   - accept: A comma‑separated list of accepted MIME types or file extensions.
 */
export default function FileUpload({ title, endpoint, accept }) {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file');
      return;
    }
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
      }
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="mb-8">
      <h2 className="text-xl font-semibold mb-2">{title}</h2>
      <form onSubmit={handleSubmit} className="flex items-center space-x-2 mb-4">
        <input
          type="file"
          accept={accept}
          onChange={(e) => setFile(e.target.files[0])}
          className="border p-2 rounded w-full"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Uploading…' : 'Upload'}
        </button>
      </form>
      {error && <p className="text-red-600 mb-2">{error}</p>}
      {result && (
        <div className="p-4 border rounded bg-gray-50">
          {/* Render thumbnail if present */}
          {'thumbnail' in result && result.thumbnail && (
            <img
              src={`data:image/png;base64,${result.thumbnail}`}
              alt="Preview"
              className="mb-4 max-w-xs"
            />
          )}
          <pre className="overflow-x-auto text-sm">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </section>
  );
}