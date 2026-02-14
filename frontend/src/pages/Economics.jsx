import React, { useState, useEffect } from 'react';
import { DollarSign, TrendingUp, TrendingDown, PieChart, Calendar, Download, Plus, Edit } from 'lucide-react';

const Economics = () => {
  const [selectedProject, setSelectedProject] = useState(null);
  const [timeRange, setTimeRange] = useState('current');
  const [economics, setEconomics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEconomics();
  }, [selectedProject, timeRange]);

  const fetchEconomics = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (selectedProject) params.append('project_id', selectedProject);
      if (timeRange) params.append('range', timeRange);

      const response = await fetch(`/api/v1/economics?${params}`);
      const data = await response.json();
      setEconomics(data);
    } catch (error) {
      console.error('Failed to fetch economics:', error);
      // Mock data
      setEconomics({
        overview: {
          total_budget: 125000000,
          actual_cost: 85000000,
          committed_cost: 92000000,
          forecast_cost: 120000000,
          variance: 5000000,
          contingency: 8000000,
          budget_utilization: 68,
        },
        cost_breakdown: [
          { category: 'Labor', budget: 45000000, actual: 30000000, percentage: 36 },
          { category: 'Materials', budget: 50000000, actual: 35000000, percentage: 40 },
          { category: 'Equipment', budget: 15000000, actual: 12000000, percentage: 12 },
          { category: 'Subcontractors', budget: 10000000, actual: 6000000, percentage: 8 },
          { category: 'Other', budget: 5000000, actual: 2000000, percentage: 4 },
        ],
        monthly_spending: [
          { month: 'Jan', budget: 8000000, actual: 7500000 },
          { month: 'Feb', budget: 9000000, actual: 8800000 },
          { month: 'Mar', budget: 10000000, actual: 9200000 },
          { month: 'Apr', budget: 11000000, actual: 10500000 },
          { month: 'May', budget: 12000000, actual: 11800000 },
          { month: 'Jun', budget: 13000000, actual: 12900000 },
        ],
        change_orders: [
          { id: 1, description: 'Foundation redesign', amount: 250000, status: 'approved', date: '2024-01-15' },
          { id: 2, description: 'Additional MEP work', amount: 180000, status: 'pending', date: '2024-02-20' },
          { id: 3, description: 'Site conditions', amount: 95000, status: 'approved', date: '2024-03-10' },
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const calculateVariancePercent = (budget, actual) => {
    return ((actual - budget) / budget * 100).toFixed(1);
  };

  const getVarianceColor = (variance) => {
    if (variance > 0) return 'text-red-600';
    if (variance < 0) return 'text-green-600';
    return 'text-gray-600';
  };

  if (loading || !economics) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <DollarSign className="w-16 h-16 mx-auto mb-4 text-green-600 animate-pulse" />
          <p className="text-gray-600 dark:text-gray-400">Loading economics data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Project Economics</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Cost tracking, budgeting, and financial analysis
          </p>
        </div>
        <div className="flex gap-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
          >
            <option value="current">Current Period</option>
            <option value="ytd">Year to Date</option>
            <option value="all">All Time</option>
          </select>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <Download className="w-5 h-5" />
            Export Report
          </button>
        </div>
      </div>

      {/* Budget Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Budget</h3>
            <DollarSign className="w-5 h-5 text-blue-600" />
          </div>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            {formatCurrency(economics.overview.total_budget)}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Original contract value
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Actual Cost</h3>
            <TrendingUp className="w-5 h-5 text-green-600" />
          </div>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            {formatCurrency(economics.overview.actual_cost)}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {economics.overview.budget_utilization}% of budget
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Committed</h3>
            <Calendar className="w-5 h-5 text-purple-600" />
          </div>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            {formatCurrency(economics.overview.committed_cost)}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Including pending invoices
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Variance</h3>
            {economics.overview.variance > 0 ? (
              <TrendingUp className="w-5 h-5 text-red-600" />
            ) : (
              <TrendingDown className="w-5 h-5 text-green-600" />
            )}
          </div>
          <p className={`text-3xl font-bold mb-2 ${getVarianceColor(economics.overview.variance)}`}>
            {formatCurrency(economics.overview.variance)}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {economics.overview.variance > 0 ? 'Over' : 'Under'} budget
          </p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cost Breakdown */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">Cost Breakdown</h2>
            <PieChart className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </div>
          <div className="space-y-4">
            {economics.cost_breakdown.map((item, idx) => (
              <div key={idx}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">{item.category}</span>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {formatCurrency(item.actual)} / {formatCurrency(item.budget)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      (item.actual / item.budget * 100) > 90 ? 'bg-red-600' :
                      (item.actual / item.budget * 100) > 75 ? 'bg-yellow-600' :
                      'bg-green-600'
                    }`}
                    style={{ width: `${Math.min((item.actual / item.budget * 100), 100)}%` }}
                  />
                </div>
                <div className="flex justify-between mt-1">
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {item.percentage}% of total
                  </span>
                  <span className={`text-xs font-medium ${getVarianceColor(item.actual - item.budget)}`}>
                    {calculateVariancePercent(item.budget, item.actual)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Monthly Spending */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">Monthly Spending</h2>
            <TrendingUp className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </div>
          <div className="space-y-3">
            {economics.monthly_spending.map((month, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{month.month}</p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    Budget: {formatCurrency(month.budget)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-gray-900 dark:text-white">
                    {formatCurrency(month.actual)}
                  </p>
                  <p className={`text-xs font-medium ${getVarianceColor(month.actual - month.budget)}`}>
                    {calculateVariancePercent(month.budget, month.actual)}%
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Change Orders */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Change Orders</h2>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <Plus className="w-5 h-5" />
            New Change Order
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Description</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {economics.change_orders.map((co) => (
                <tr key={co.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    CO-{co.id.toString().padStart(3, '0')}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                    {co.description}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                    {formatCurrency(co.amount)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      co.status === 'approved'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : co.status === 'pending'
                        ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                        : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    }`}>
                      {co.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {new Date(co.date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button className="text-blue-600 hover:text-blue-900">
                      <Edit className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Contingency & Forecast */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Contingency</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Original Contingency</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {formatCurrency(economics.overview.contingency)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Remaining</span>
              <span className="text-sm font-bold text-green-600">
                {formatCurrency(economics.overview.contingency * 0.65)}
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
              <div className="bg-green-600 h-3 rounded-full" style={{ width: '65%' }} />
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">65% remaining</p>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Forecast</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Forecast at Completion</span>
              <span className="text-sm font-bold text-gray-900 dark:text-white">
                {formatCurrency(economics.overview.forecast_cost)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">vs Budget</span>
              <span className={`text-sm font-bold ${getVarianceColor(economics.overview.forecast_cost - economics.overview.total_budget)}`}>
                {formatCurrency(economics.overview.forecast_cost - economics.overview.total_budget)}
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Based on current trends and commitments
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Economics;
