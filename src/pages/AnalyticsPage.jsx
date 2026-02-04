import React, { useEffect, useState } from 'react';

/**
 * AnalyticsPage displays high‑level project analytics including overview,
 * key metrics, cost projections and risk assessments.  The data is
 * fetched from the backend's analytics endpoints.  In the community
 * edition these endpoints return stubbed data; in a full deployment
 * they would be backed by a proper analytics engine.
 */
export default function AnalyticsPage() {
  const [overview, setOverview] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [projection, setProjection] = useState(null);
  const [risks, setRisks] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [oRes, mRes, pRes, rRes] = await Promise.all([
          fetch('/api/v1/analytics/overview'),
          fetch('/api/v1/analytics/key-metrics'),
          fetch('/api/v1/analytics/cost-projection'),
          fetch('/api/v1/analytics/risk-assessment'),
        ]);
        if (!oRes.ok || !mRes.ok || !pRes.ok || !rRes.ok) {
          throw new Error('Failed to fetch analytics');
        }
        const [o, m, p, r] = await Promise.all([
          oRes.json(),
          mRes.json(),
          pRes.json(),
          rRes.json(),
        ]);
        setOverview(o);
        setMetrics(m);
        setProjection(p);
        setRisks(r);
      } catch (err) {
        console.error(err);
        setError(err.message);
      }
    }
    fetchData();
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Project Analytics</h1>
      {error && (
        <p className="text-red-600 mb-4">Error loading analytics: {error}</p>
      )}
      {!error && !overview && <p>Loading analytics…</p>}
      {overview && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-2">Overview</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 border rounded">
              <span className="font-medium">Total tasks:</span> {overview.total_tasks}
            </div>
            <div className="p-4 border rounded">
              <span className="font-medium">Completed tasks:</span> {overview.completed_tasks}
            </div>
            <div className="p-4 border rounded">
              <span className="font-medium">Pending tasks:</span> {overview.pending_tasks}
            </div>
            <div className="p-4 border rounded">
              <span className="font-medium">Schedule progress:</span> {Math.round((overview.schedule_progress || 0) * 100)}%
            </div>
            <div className="p-4 border rounded">
              <span className="font-medium">Cost incurred:</span> SAR {overview.cost_incurred?.toLocaleString()}
            </div>
            <div className="p-4 border rounded">
              <span className="font-medium">Budget:</span> SAR {overview.budget?.toLocaleString()}
            </div>
          </div>
        </section>
      )}
      {metrics && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-2">Key Metrics</h2>
          <div className="grid grid-cols-2 gap-4">
            {Object.entries(metrics.kpis || {}).map(([name, value]) => (
              <div key={name} className="p-4 border rounded">
                <span className="font-medium capitalize">{name.replace(/_/g, ' ')}:</span> {value}
              </div>
            ))}
          </div>
        </section>
      )}
      {projection && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-2">Cost Projection</h2>
          <p className="mb-2">
            <span className="font-medium">Remaining budget:</span> SAR {projection.remaining_budget?.toLocaleString()}
          </p>
          <p className="mb-2">
            <span className="font-medium">Estimated weeks remaining:</span> {projection.estimated_weeks_remaining}
          </p>
          <p className="mb-2">
            <span className="font-medium">Current burn rate:</span> SAR {projection.burn_rate?.toLocaleString()} per week
          </p>
          <p className="text-gray-600 text-sm">{projection.note}</p>
        </section>
      )}
      {risks && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-2">Risk Assessment</h2>
          <div className="space-y-3">
            {(risks.risks || []).map((risk) => (
              <div key={risk.id} className="p-4 border rounded">
                <h3 className="font-medium">{risk.title}</h3>
                <p className="text-sm text-gray-600 mb-1">
                  <span className="font-medium">Severity:</span> {risk.severity} &mdash; <span className="font-medium">Probability:</span> {Math.round((risk.probability || 0) * 100)}%
                </p>
                <p className="text-sm">{risk.mitigation}</p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}