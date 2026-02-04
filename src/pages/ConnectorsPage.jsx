import React, { useEffect, useState } from 'react';

/**
 * ConnectorsPage lists the configured status of optional external services
 * such as Aconex, Primavera, Teams, etc.  The backend returns whether
 * each service is configured based on environment variables.  In a full
 * deployment these statuses would reflect real health checks.
 */
export default function ConnectorsPage() {
  const [connectors, setConnectors] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchConnectors() {
      try {
        const res = await fetch('/api/connectors/list');
        if (!res.ok) throw new Error('Failed to load connectors');
        const data = await res.json();
        setConnectors(data);
      } catch (err) {
        console.error(err);
        setError(err.message);
      }
    }
    fetchConnectors();
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Connector Status</h1>
      {error && <p className="text-red-600 mb-4">{error}</p>}
      {!error && !connectors && <p>Loading connectors…</p>}
      {connectors && (
        <table className="min-w-full border">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 border-b text-left">Connector</th>
              <th className="px-4 py-2 border-b text-left">Status</th>
              <th className="px-4 py-2 border-b text-left">Details</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(connectors).map(([name, info]) => (
              <tr key={name} className="odd:bg-white even:bg-gray-50">
                <td className="px-4 py-2 border-b capitalize">{name.replace('_', ' ')}</td>
                <td className="px-4 py-2 border-b">
                  <span
                    className={`px-2 py-1 text-xs rounded ${
                      info.status === 'connected'
                        ? 'bg-green-200 text-green-800'
                        : info.status === 'configured'
                        ? 'bg-blue-200 text-blue-800'
                        : info.status === 'stubbed'
                        ? 'bg-yellow-200 text-yellow-800'
                        : 'bg-gray-200 text-gray-700'
                    }`}
                  >
                    {info.status}
                  </span>
                </td>
                <td className="px-4 py-2 border-b text-sm">
                  {info.details ? JSON.stringify(info.details) : info.error || ''}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}