import React, { useState, useEffect } from 'react';

/**
 * ScheduleUpload handles the lifecycle of uploading a project schedule and
 * retrieving its asynchronous analysis result.  It accepts a XER, XML or
 * MPP file, posts it to the backend, and polls the job status endpoint
 * until processing completes.  The computed metrics (e.g. critical path)
 * are then displayed as formatted JSON.
 */
export default function ScheduleUpload() {
  const [file, setFile] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  // Poll the job status whenever a new job is submitted and still processing
  useEffect(() => {
    let intervalId;
    if (jobId && status === 'processing') {
      intervalId = setInterval(async () => {
        try {
          const res = await fetch(`/api/v1/schedule/status/${jobId}`);
          const data = await res.json();
          if (!res.ok) {
            throw new Error(data.detail || 'Failed to fetch job status');
          }
          if (data.status === 'completed') {
            setStatus('completed');
            setResult(data.result);
            clearInterval(intervalId);
          } else if (data.status === 'failed') {
            setStatus('failed');
            setError(data.error || 'Schedule analysis failed');
            clearInterval(intervalId);
          } else {
            // still processing
            setStatus('processing');
          }
        } catch (err) {
          setStatus('failed');
          setError(err.message);
          clearInterval(intervalId);
        }
      }, 3000);
    }
    return () => clearInterval(intervalId);
  }, [jobId, status]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file');
      return;
    }
    setError('');
    setResult(null);
    setJobId(null);
    setStatus(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const resp = await fetch('/api/v1/schedule/analyze', {
        method: 'POST',
        body: formData,
      });
      const data = await resp.json();
      if (!resp.ok) {
          throw new Error(data.detail || 'Upload failed');
      }
      setJobId(data.job_id);
      setStatus(data.status);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="mb-8">
      <form onSubmit={handleSubmit} className="flex items-center space-x-2 mb-4">
        <input
          type="file"
          accept=".xer,.xml,.mpp,application/octet-stream,application/xml,text/xml"
          onChange={(e) => setFile(e.target.files[0])}
          className="border p-2 rounded w-full"
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          disabled={!file}
        >
          Upload
        </button>
      </form>
      {status && <p className="mb-2">Status: {status}</p>}
      {error && <p className="text-red-600 mb-2">{error}</p>}
      {result && (
        <div className="p-4 border rounded bg-gray-50">
          <pre className="overflow-x-auto text-sm">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}