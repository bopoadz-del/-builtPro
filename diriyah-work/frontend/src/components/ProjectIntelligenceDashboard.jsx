import React, { useState, useEffect, useMemo } from 'react';

/**
 * ProjectIntelligenceDashboard - Real-time project analytics and forecasting
 * 
 * Features:
 * - Progress tracking with SPI/CPI gauges
 * - Schedule and cost forecasts
 * - Anomaly alerts
 * - Trend charts
 * - EVM metrics
 */

// Simple gauge component
const Gauge = ({ value, label, color = '#a67c52', max = 2 }) => {
  const percentage = Math.min((value / max) * 100, 100);
  const rotation = (percentage / 100) * 180 - 90;
  
  const getColor = () => {
    if (value >= 1.0) return '#22c55e'; // Green
    if (value >= 0.85) return '#eab308'; // Yellow
    return '#ef4444'; // Red
  };

  return (
    <div className="flex flex-col items-center">
      <div className="relative h-20 w-40 overflow-hidden">
        <div className="absolute inset-0 rounded-t-full border-8 border-gray-200" />
        <div
          className="absolute inset-0 rounded-t-full border-8 border-transparent"
          style={{
            borderTopColor: getColor(),
            borderLeftColor: getColor(),
            transform: `rotate(${rotation}deg)`,
            transformOrigin: 'bottom center',
          }}
        />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-center">
          <p className="text-2xl font-bold" style={{ color: getColor() }}>
            {value.toFixed(2)}
          </p>
        </div>
      </div>
      <p className="mt-2 text-sm font-medium text-gray-600">{label}</p>
    </div>
  );
};

// Simple bar chart
const BarChart = ({ data, title }) => {
  const maxValue = Math.max(...data.map(d => d.value), 1);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <h3 className="mb-4 font-semibold text-gray-900">{title}</h3>
      <div className="space-y-3">
        {data.map((item, idx) => (
          <div key={idx}>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">{item.label}</span>
              <span className="font-medium">{item.value}</span>
            </div>
            <div className="mt-1 h-2 overflow-hidden rounded-full bg-gray-200">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${(item.value / maxValue) * 100}%`,
                  backgroundColor: item.color || '#a67c52',
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Progress trend mini-chart
const TrendLine = ({ data, height = 60 }) => {
  if (!data || data.length < 2) return null;

  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const points = data.map((value, i) => {
    const x = (i / (data.length - 1)) * 100;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg className="w-full" height={height} viewBox={`0 0 100 ${height}`} preserveAspectRatio="none">
      <polyline
        fill="none"
        stroke="#a67c52"
        strokeWidth="2"
        points={points}
      />
    </svg>
  );
};

// Status badge
const StatusBadge = ({ status }) => {
  const styles = {
    healthy: 'bg-green-100 text-green-800',
    at_risk: 'bg-yellow-100 text-yellow-800',
    critical: 'bg-red-100 text-red-800',
    warning: 'bg-orange-100 text-orange-800',
  };

  return (
    <span className={`rounded-full px-3 py-1 text-sm font-medium ${styles[status] || styles.warning}`}>
      {status.replace('_', ' ').toUpperCase()}
    </span>
  );
};

// Alert card
const AlertCard = ({ alert }) => {
  const severityStyles = {
    critical: 'border-red-300 bg-red-50',
    high: 'border-orange-300 bg-orange-50',
    medium: 'border-yellow-300 bg-yellow-50',
    low: 'border-gray-300 bg-gray-50',
  };

  const severityIcons = {
    critical: '🚨',
    high: '⚠️',
    medium: '⚡',
    low: 'ℹ️',
  };

  return (
    <div className={`rounded-lg border-l-4 p-3 ${severityStyles[alert.severity]}`}>
      <div className="flex items-start gap-2">
        <span>{severityIcons[alert.severity]}</span>
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-900">{alert.message}</p>
          <p className="mt-1 text-xs text-gray-500">
            {alert.type} • {alert.timestamp ? new Date(alert.timestamp).toLocaleDateString() : 'Recent'}
          </p>
        </div>
      </div>
    </div>
  );
};

// Metric card
const MetricCard = ({ title, value, subtitle, trend, icon }) => (
  <div className="rounded-lg border border-gray-200 bg-white p-4">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm text-gray-500">{title}</p>
        <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
        {subtitle && <p className="mt-1 text-sm text-gray-500">{subtitle}</p>}
      </div>
      {icon && <span className="text-2xl">{icon}</span>}
    </div>
    {trend && (
      <div className={`mt-2 flex items-center text-sm ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
        <span>{trend > 0 ? '↑' : '↓'}</span>
        <span className="ml-1">{Math.abs(trend)}% vs last week</span>
      </div>
    )}
  </div>
);

export default function ProjectIntelligenceDashboard({ projectId = 'demo_project' }) {
  const [forecast, setForecast] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  // Demo data for visualization
  const demoData = useMemo(() => ({
    progress: {
      current: 47,
      planned: 52,
      trend: [35, 38, 40, 43, 45, 47],
    },
    cost: {
      budget: 63000000,
      actual: 28500000,
      committed: 5200000,
    },
    schedule: {
      startDate: '2024-01-15',
      endDate: '2025-12-31',
      forecastEnd: '2026-02-15',
      delayDays: 46,
    },
    evm: {
      spi: 0.90,
      cpi: 0.95,
      ev: 29610000,
      pv: 32760000,
      ac: 31168000,
    },
    anomalies: [
      { severity: 'high', type: 'schedule', message: 'Foundation work 12 days behind schedule' },
      { severity: 'medium', type: 'cost', message: 'Material costs 8% over budget' },
      { severity: 'low', type: 'safety', message: 'PPE compliance check due' },
    ],
  }), []);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        // Fetch forecast
        const forecastRes = await fetch('/api/forecast/project', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            project_name: projectId,
            planned_end_date: demoData.schedule.endDate,
            current_progress: demoData.progress.current,
            planned_progress: demoData.progress.planned,
            project_duration_days: 700,
            elapsed_days: 385,
            budget: demoData.cost.budget,
            actual_cost: demoData.cost.actual,
          }),
        });
        
        if (forecastRes.ok) {
          const data = await forecastRes.json();
          setForecast(data);
        }

        // Fetch anomalies
        const anomalyRes = await fetch('/api/anomalies/simulate?days=7&project_id=' + projectId, {
          method: 'POST',
        });
        
        if (anomalyRes.ok) {
          const data = await anomalyRes.json();
          setAnomalies(data.findings?.slice(0, 5) || demoData.anomalies);
        } else {
          setAnomalies(demoData.anomalies);
        }
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
        setAnomalies(demoData.anomalies);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [projectId, demoData]);

  const evmData = forecast?.evm_metrics || demoData.evm;
  const scheduleData = forecast?.schedule_forecast || {};
  const costData = forecast?.cost_forecast || {};
  const overallAssessment = forecast?.overall_assessment || { health_score: 75, health_status: 'at_risk' };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-[#a67c52]" />
          <span className="text-gray-600">Loading dashboard...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Project Intelligence</h1>
          <p className="text-gray-500">Real-time analytics and forecasting</p>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge status={overallAssessment.health_status} />
          <span className="text-2xl font-bold text-gray-900">
            {overallAssessment.health_score}
          </span>
          <span className="text-sm text-gray-500">Health Score</span>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-6">
          {['overview', 'schedule', 'cost', 'anomalies'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`border-b-2 pb-3 text-sm font-medium capitalize transition-colors ${
                activeTab === tab
                  ? 'border-[#a67c52] text-[#a67c52]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <MetricCard
              title="Progress"
              value={`${demoData.progress.current}%`}
              subtitle={`Target: ${demoData.progress.planned}%`}
              icon="📊"
            />
            <MetricCard
              title="Budget Spent"
              value={`${Math.round((demoData.cost.actual / demoData.cost.budget) * 100)}%`}
              subtitle={`SAR ${(demoData.cost.actual / 1000000).toFixed(1)}M of ${(demoData.cost.budget / 1000000).toFixed(1)}M`}
              icon="💰"
            />
            <MetricCard
              title="Schedule Delay"
              value={`${scheduleData.delay_days || demoData.schedule.delayDays} days`}
              subtitle={scheduleData.risk_level || 'Medium risk'}
              icon="📅"
            />
            <MetricCard
              title="Active Alerts"
              value={anomalies.length}
              subtitle={anomalies.filter(a => a.severity === 'critical' || a.severity === 'high').length + ' high priority'}
              icon="🔔"
            />
          </div>

          {/* Performance Indices */}
          <div className="rounded-lg border border-gray-200 bg-white p-6">
            <h3 className="mb-6 text-lg font-semibold text-gray-900">Performance Indices</h3>
            <div className="flex justify-around">
              <Gauge value={evmData.schedule_performance_index || evmData.spi} label="SPI (Schedule)" />
              <Gauge value={evmData.cost_performance_index || evmData.cpi} label="CPI (Cost)" />
            </div>
            <div className="mt-6 grid grid-cols-2 gap-4 text-center text-sm md:grid-cols-4">
              <div>
                <p className="text-gray-500">Earned Value</p>
                <p className="font-semibold">SAR {((evmData.earned_value || evmData.ev) / 1000000).toFixed(1)}M</p>
              </div>
              <div>
                <p className="text-gray-500">Planned Value</p>
                <p className="font-semibold">SAR {((evmData.planned_value || evmData.pv) / 1000000).toFixed(1)}M</p>
              </div>
              <div>
                <p className="text-gray-500">Actual Cost</p>
                <p className="font-semibold">SAR {((evmData.actual_cost || evmData.ac) / 1000000).toFixed(1)}M</p>
              </div>
              <div>
                <p className="text-gray-500">EAC</p>
                <p className="font-semibold">SAR {((evmData.estimate_at_completion || demoData.cost.budget * 1.05) / 1000000).toFixed(1)}M</p>
              </div>
            </div>
          </div>

          {/* Progress Trend & Alerts */}
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-lg border border-gray-200 bg-white p-4">
              <h3 className="mb-4 font-semibold text-gray-900">Progress Trend</h3>
              <TrendLine data={demoData.progress.trend} height={80} />
              <div className="mt-4 flex justify-between text-sm text-gray-500">
                <span>6 weeks ago</span>
                <span>Current</span>
              </div>
            </div>

            <div className="rounded-lg border border-gray-200 bg-white p-4">
              <h3 className="mb-4 font-semibold text-gray-900">Recent Alerts</h3>
              <div className="space-y-2">
                {anomalies.slice(0, 3).map((alert, idx) => (
                  <AlertCard key={idx} alert={alert} />
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Schedule Tab */}
      {activeTab === 'schedule' && (
        <div className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-lg border border-gray-200 bg-white p-6">
              <h3 className="mb-4 text-lg font-semibold text-gray-900">Schedule Forecast</h3>
              <div className="space-y-4">
                <div className="flex justify-between border-b border-gray-100 pb-3">
                  <span className="text-gray-500">Original End Date</span>
                  <span className="font-semibold">{scheduleData.original_end_date || demoData.schedule.endDate}</span>
                </div>
                <div className="flex justify-between border-b border-gray-100 pb-3">
                  <span className="text-gray-500">Forecasted End Date</span>
                  <span className="font-semibold text-orange-600">{scheduleData.forecasted_end_date || demoData.schedule.forecastEnd}</span>
                </div>
                <div className="flex justify-between border-b border-gray-100 pb-3">
                  <span className="text-gray-500">Delay</span>
                  <span className="font-semibold">{scheduleData.delay_days || demoData.schedule.delayDays} days</span>
                </div>
                <div className="flex justify-between border-b border-gray-100 pb-3">
                  <span className="text-gray-500">On-Time Probability</span>
                  <span className="font-semibold">{Math.round((scheduleData.probability_on_time || 0.35) * 100)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Risk Level</span>
                  <StatusBadge status={scheduleData.risk_level || 'at_risk'} />
                </div>
              </div>
            </div>

            <div className="rounded-lg border border-gray-200 bg-white p-6">
              <h3 className="mb-4 text-lg font-semibold text-gray-900">Recommendations</h3>
              <ul className="space-y-3">
                {(scheduleData.recommendations || [
                  'Consider schedule acceleration options',
                  'Review critical path for fast-tracking opportunities',
                  'Initiate recovery plan with stakeholders',
                ]).map((rec, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm">
                    <span className="mt-0.5 text-[#a67c52]">•</span>
                    <span className="text-gray-700">{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Cost Tab */}
      {activeTab === 'cost' && (
        <div className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-lg border border-gray-200 bg-white p-6">
              <h3 className="mb-4 text-lg font-semibold text-gray-900">Cost Forecast</h3>
              <div className="space-y-4">
                <div className="flex justify-between border-b border-gray-100 pb-3">
                  <span className="text-gray-500">Original Budget</span>
                  <span className="font-semibold">SAR {((costData.original_budget || demoData.cost.budget) / 1000000).toFixed(1)}M</span>
                </div>
                <div className="flex justify-between border-b border-gray-100 pb-3">
                  <span className="text-gray-500">Forecasted Cost</span>
                  <span className="font-semibold text-orange-600">SAR {((costData.forecasted_cost || demoData.cost.budget * 1.05) / 1000000).toFixed(1)}M</span>
                </div>
                <div className="flex justify-between border-b border-gray-100 pb-3">
                  <span className="text-gray-500">Variance</span>
                  <span className="font-semibold">{(costData.variance_percent || 5).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between border-b border-gray-100 pb-3">
                  <span className="text-gray-500">Within Budget Probability</span>
                  <span className="font-semibold">{Math.round((costData.probability_within_budget || 0.55) * 100)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Risk Level</span>
                  <StatusBadge status={costData.risk_level || 'medium'} />
                </div>
              </div>
            </div>

            <BarChart
              title="Cost Breakdown"
              data={[
                { label: 'Structural', value: 12.5, color: '#3b82f6' },
                { label: 'MEP', value: 8.2, color: '#22c55e' },
                { label: 'Finishes', value: 4.1, color: '#eab308' },
                { label: 'External', value: 3.7, color: '#a67c52' },
              ]}
            />
          </div>
        </div>
      )}

      {/* Anomalies Tab */}
      {activeTab === 'anomalies' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">All Alerts</h3>
            <div className="flex gap-2 text-sm">
              <span className="rounded-full bg-red-100 px-3 py-1 text-red-800">
                {anomalies.filter(a => a.severity === 'critical').length} Critical
              </span>
              <span className="rounded-full bg-orange-100 px-3 py-1 text-orange-800">
                {anomalies.filter(a => a.severity === 'high').length} High
              </span>
              <span className="rounded-full bg-yellow-100 px-3 py-1 text-yellow-800">
                {anomalies.filter(a => a.severity === 'medium').length} Medium
              </span>
            </div>
          </div>

          <div className="space-y-3">
            {anomalies.map((alert, idx) => (
              <AlertCard key={idx} alert={alert} />
            ))}
            {anomalies.length === 0 && (
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
                <p className="text-gray-500">No anomalies detected</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
