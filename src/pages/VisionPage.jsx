import React, { useEffect, useState } from 'react';

/**
 * VisionPage displays the diagnostic status of the vision service.  The
 * backend endpoint returns whether the vision connector is configured
 * and healthy.  In the stub implementation it always reports
 * connected.  A full implementation could also allow image upload for
 * analysis.
 */
export default function VisionPage() {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchStatus() {
      try {
        const res = await fetch('/api/v1/vision/diagnostics');
        if (!res.ok) throw new Error('Failed to load vision diagnostics');
        const data = await res.json();
        setStatus(data);
      } catch (err) {
        console.error(err);
        setError(err.message);
      }
    }
    fetchStatus();
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Vision Diagnostics</h1>
      {error && <p className="text-red-600 mb-4">{error}</p>}
      {!error && !status && <p>Checking vision service…</p>}
      {status && (
        <div className="p-4 border rounded bg-gray-50">
          <p>
            <span className="font-medium">Status:</span> {status.status}
          </p>
          {status.detail && (
            <p>
              <span className="font-medium">Detail:</span> {status.detail}
            </p>
          )}
        </div>
      )}
    </div>
  );
}